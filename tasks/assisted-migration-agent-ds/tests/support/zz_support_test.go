package hiddencheck

import (
	"bytes"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"database/sql"
	"encoding/json"
	"encoding/pem"
	"io"
	"math/big"
	"net"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"os"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"github.com/vmware/govmomi/simulator"

	"github.com/kubev2v/migration-planner/pkg/duckdb_parser"
	ddmodels "github.com/kubev2v/migration-planner/pkg/duckdb_parser/models"

	api "github.com/kubev2v/assisted-migration-agent/api/v1"
	"github.com/kubev2v/assisted-migration-agent/internal/config"
	handlers "github.com/kubev2v/assisted-migration-agent/internal/handlers/v1"
	"github.com/kubev2v/assisted-migration-agent/internal/models"
	"github.com/kubev2v/assisted-migration-agent/internal/services"
	"github.com/kubev2v/assisted-migration-agent/internal/store"
	"github.com/kubev2v/assisted-migration-agent/internal/store/migrations"
	"github.com/kubev2v/assisted-migration-agent/pkg/console"
)

func TestMain(m *testing.M) {
	if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
		handlers.RegisterValidators(v)
	}
	gin.SetMode(gin.TestMode)
	os.Exit(m.Run())
}

// plainValidator accepts every VM without concerns.
type plainValidator struct{}

func (plainValidator) Validate(context.Context, ddmodels.VM) ([]ddmodels.Concern, error) { return nil, nil }

var _ duckdb_parser.Validator = plainValidator{}

// identity is a TLS server identity: a CA and a leaf certificate it signs.
type identity struct {
	caPEM []byte
	leaf  tls.Certificate
}

func newIdentity(t *testing.T, dnsName string, ipSAN bool) *identity {
	t.Helper()
	caKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatalf("generate CA key: %v", err)
	}
	caTmpl := &x509.Certificate{
		SerialNumber:          big.NewInt(1),
		Subject:               pkix.Name{CommonName: "test-ca"},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().Add(2 * time.Hour),
		IsCA:                  true,
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageDigitalSignature,
		BasicConstraintsValid: true,
	}
	caDER, err := x509.CreateCertificate(rand.Reader, caTmpl, caTmpl, &caKey.PublicKey, caKey)
	if err != nil {
		t.Fatalf("create CA: %v", err)
	}
	caCert, err := x509.ParseCertificate(caDER)
	if err != nil {
		t.Fatalf("parse CA: %v", err)
	}

	leafKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatalf("generate leaf key: %v", err)
	}
	leafTmpl := &x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject:      pkix.Name{CommonName: dnsName},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(2 * time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		DNSNames:     []string{dnsName},
	}
	if ipSAN {
		leafTmpl.IPAddresses = []net.IP{net.ParseIP("127.0.0.1")}
	}
	leafDER, err := x509.CreateCertificate(rand.Reader, leafTmpl, caCert, &leafKey.PublicKey, caKey)
	if err != nil {
		t.Fatalf("create leaf: %v", err)
	}

	return &identity{
		caPEM: pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caDER}),
		leaf:  tls.Certificate{Certificate: [][]byte{leafDER}, PrivateKey: leafKey},
	}
}

// tlsOracle is a TLS endpoint that counts the sessions a client completes with
// it. A session counts only after the handshake succeeds, so a client that
// rejects the certificate leaves the count at zero.
type tlsOracle struct {
	mu        sync.Mutex
	completed int
	failed    int
	cert      atomic.Pointer[tls.Certificate]
	srv       *http.Server
	url       *url.URL
}

type countingListener struct {
	net.Listener
	o *tlsOracle
}

func (l *countingListener) Accept() (net.Conn, error) {
	c, err := l.Listener.Accept()
	if err != nil {
		return nil, err
	}
	return &countingConn{Conn: c, o: l.o}, nil
}

type countingConn struct {
	net.Conn
	o    *tlsOracle
	once sync.Once
}

func (c *countingConn) Read(p []byte) (int, error) {
	c.once.Do(func() {
		if tc, ok := c.Conn.(*tls.Conn); ok {
			if err := tc.Handshake(); err != nil {
				c.o.mu.Lock()
				c.o.failed++
				c.o.mu.Unlock()
				return
			}
			c.o.mu.Lock()
			c.o.completed++
			c.o.mu.Unlock()
		}
	})
	return c.Conn.Read(p)
}

func newTLSOracle(t *testing.T, id *identity, backend http.Handler) *tlsOracle {
	t.Helper()
	o := &tlsOracle{}
	o.cert.Store(&id.leaf)
	cfg := &tls.Config{
		GetCertificate: func(*tls.ClientHelloInfo) (*tls.Certificate, error) { return o.cert.Load(), nil },
		MinVersion:     tls.VersionTLS12,
	}
	raw, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	o.url = &url.URL{Scheme: "https", Host: raw.Addr().String(), Path: "/sdk"}
	o.srv = &http.Server{Handler: backend}
	go func() { _ = o.srv.Serve(&countingListener{Listener: tls.NewListener(raw, cfg), o: o}) }()
	t.Cleanup(func() { _ = o.srv.Close() })
	return o
}

func (o *tlsOracle) URL() string { return o.url.String() }

func (o *tlsOracle) Completed() int {
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.completed
}

func (o *tlsOracle) Attempted() int {
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.completed + o.failed
}

func (o *tlsOracle) Rotate(t *testing.T, id *identity) {
	o.cert.Store(&id.leaf)
}

// rejectingBackend answers every request with a server error; clients that get
// this far have already completed the TLS handshake, which is what matters.
func rejectingBackend() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusInternalServerError) })
}

// liveBackend serves a real vCenter inventory simulator through a reverse proxy.
func liveBackend(t *testing.T) (http.Handler, func()) {
	t.Helper()
	m := simulator.VPX()
	if err := m.Create(); err != nil {
		t.Fatalf("start vcenter simulator: %v", err)
	}
	m.Service.RegisterEndpoints = true
	sim := m.Service.NewServer()
	target := &url.URL{Scheme: sim.URL.Scheme, Host: sim.URL.Host}
	proxy := httputil.NewSingleHostReverseProxy(target)
	return proxy, func() {
		sim.Close()
		m.Remove()
	}
}

func waitFor(d time.Duration, cond func() bool) {
	deadline := time.Now().Add(d)
	for time.Now().Before(deadline) {
		if cond() {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
}

// settleAsync gives background work enough time to reach the endpoint.
func settleAsync(o *tlsOracle) {
	waitFor(8*time.Second, func() bool { return o.Attempted() > 0 })
	time.Sleep(200 * time.Millisecond)
}

func waitConnected(o *tlsOracle) {
	waitFor(8*time.Second, func() bool { return o.Completed() > 0 })
}

// ---- agent stack ----

type stack struct {
	db  *sql.DB
	st  *store.Store
	URL string
}

func newStack(t *testing.T) *stack {
	t.Helper()
	ctx := context.Background()
	db, err := store.NewDB(nil, ":memory:")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	if err := migrations.Run(ctx, db); err != nil {
		t.Fatalf("migrate store: %v", err)
	}
	st := store.NewStore(db, plainValidator{})

	consoleSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	cc, err := console.NewConsoleClient(consoleSrv.URL, "")
	if err != nil {
		t.Fatalf("console client: %v", err)
	}

	cfg := config.NewConfigurationWithOptionsAndDefaults(config.WithAgent(config.Agent{
		ID:       uuid.NewString(),
		SourceID: uuid.NewString(),
		Mode:     "disconnected",
	}))
	cfg.Agent.DataFolder = t.TempDir()

	mgr := services.NewServiceManager(
		services.WithConfig(cfg),
		services.WithStore(st),
		services.WithConsoleClient(cc),
	)
	if err := mgr.Initialize(); err != nil {
		t.Fatalf("initialize services: %v", err)
	}

	h := handlers.NewHandler(*cfg).
		WithConsoleService(mgr.ConsoleService()).
		WithCollectorService(mgr.CollectorService()).
		WithInventoryService(mgr.InventoryService()).
		WithVMService(mgr.VirtualMachineService()).
		WithInspectorService(mgr.InspectorService()).
		WithVddkService(mgr.VddkService()).
		WithGroupService(mgr.GroupService()).
		WithRightsizingService(mgr.RightsizingService()).
		WithForecasterService(mgr.ForecasterService()).
		WithApplicationService(mgr.ApplicationService())

	r := gin.New()
	r.Use(gin.Recovery())
	api.RegisterHandlers(r, h)
	hs := httptest.NewServer(r)

	s := &stack{db: db, st: st, URL: hs.URL}
	t.Cleanup(func() {
		hs.Close()
		consoleSrv.Close()
		mgr.Stop(context.Background())
		_ = db.Close()
	})
	return s
}

// seedVddk records an uploaded VDDK so inspection requests pass their precondition.
func (s *stack) seedVddk(t *testing.T) {
	t.Helper()
	if err := s.st.Vddk().Save(context.Background(), &models.VddkStatus{
		Version: "8.0.3",
		Md5:     "d41d8cd98f00b204e9800998ecf8427e",
	}); err != nil {
		t.Fatalf("seed vddk: %v", err)
	}
}

// seedVM records an inventory VM so inspection work can be scheduled for it.
func (s *stack) seedVM(t *testing.T, id, name string) {
	t.Helper()
	_, err := s.db.Exec(
		`INSERT INTO vinfo ("VM ID", "VM", "Powerstate", "Cluster", "Memory") VALUES (?, ?, 'poweredOn', 'cluster-a', 4096)`,
		id, name,
	)
	if err != nil {
		t.Fatalf("seed vm: %v", err)
	}
}

func (s *stack) request(t *testing.T, method, path string, body any) (int, string) {
	t.Helper()
	var rd io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal request: %v", err)
		}
		rd = bytes.NewReader(b)
	}
	req, err := http.NewRequest(method, s.URL+path, rd)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("request %s %s: %v", method, path, err)
	}
	defer func() { _ = resp.Body.Close() }()
	out, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(out)
}

func credentials(url string) map[string]any {
	return map[string]any{"url": url, "username": "user", "password": "pass"}
}

func forecasterBody(url string, extra map[string]any) map[string]any {
	creds := credentials(url)
	for k, v := range extra {
		creds[k] = v
	}
	return map[string]any{
		"pairs": []map[string]any{{
			"name":            "pair-1",
			"sourceDatastore": "LocalDS_0",
			"targetDatastore": "LocalDS_0",
		}},
		"credentials": creds,
	}
}

func inspectorBody(url string, vmIDs []string) map[string]any {
	return map[string]any{"vmIds": vmIDs, "credentials": credentials(url)}
}

// assertBlocked fails when the agent completed a TLS session it should have refused.
func assertBlocked(t *testing.T, code int, o *tlsOracle, async bool) {
	t.Helper()
	if async && code < 400 {
		settleAsync(o)
	}
	if got := o.Completed(); got != 0 {
		t.Fatalf("the agent completed %d TLS session(s) with a server whose certificate should not have been accepted (response %d)", got, code)
	}
}

// assertClientError fails unless the request failed as a client error.
func assertClientError(t *testing.T, code int, body string) {
	t.Helper()
	if code < 400 || code >= 500 {
		t.Fatalf("expected a client error, got %d: %s", code, body)
	}
}

// assertConnected fails unless the agent completed a TLS session.
func assertConnected(t *testing.T, o *tlsOracle, async bool) {
	t.Helper()
	if async {
		waitConnected(o)
	}
	if got := o.Completed(); got == 0 {
		t.Fatal("the agent did not complete a TLS session with a certificate it should accept")
	}
}
