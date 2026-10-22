package server

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/traefik/paerser/flag"
	"github.com/traefik/traefik/v2/pkg/config/static"
	tcprouter "github.com/traefik/traefik/v2/pkg/server/router/tcp"
)

// zzBackend records the last request that the entry point routed.
type zzBackend struct {
	mu      sync.Mutex
	reached bool
	header  http.Header
}

func (b *zzBackend) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	b.mu.Lock()
	b.reached = true
	b.header = req.Header.Clone()
	b.mu.Unlock()
	rw.WriteHeader(http.StatusOK)
}

func (b *zzBackend) take() (bool, http.Header) {
	b.mu.Lock()
	defer b.mu.Unlock()
	reached, header := b.reached, b.header
	b.reached, b.header = false, nil
	return reached, header
}

// zzLoadEntryPoints loads the static configuration from command-line flags, as the traefik
// command does, and creates the entry points from it.
func zzLoadEntryPoints(t *testing.T, flags ...string) (TCPEntryPoints, error) {
	t.Helper()
	cfg := &static.Configuration{}
	args := append([]string{"--entryPoints.web.address=127.0.0.1:0"}, flags...)
	if err := flag.Decode(args, cfg); err != nil {
		return nil, fmt.Errorf("loading flags: %w", err)
	}
	return NewTCPEntryPoints(cfg.EntryPoints, nil)
}

// zzStart starts the "web" entry point with backend as the routed handler and returns its address.
func zzStart(t *testing.T, eps TCPEntryPoints, backend http.Handler) string {
	t.Helper()
	ep, ok := eps["web"]
	if !ok {
		t.Fatal("entry point web not created")
	}
	router, err := tcprouter.NewRouter()
	if err != nil {
		t.Fatal(err)
	}
	router.SetHTTPHandler(backend)
	go ep.Start(t.Context())
	ep.SwitchRouter(router)
	t.Cleanup(func() { ep.Shutdown(t.Context()) })

	addr := ep.listener.Addr().String()
	for range 50 {
		conn, err := net.Dial("tcp", addr)
		if err == nil {
			_ = conn.Close()
			return addr
		}
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatal("entry point never started")
	return ""
}

// zzRawGet sends one HTTP/1.1 request whose header lines are written exactly as given and returns the status.
func zzRawGet(t *testing.T, addr string, lines ...string) int {
	t.Helper()
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(10 * time.Second))

	var b strings.Builder
	b.WriteString("GET /zz HTTP/1.1\r\nHost: zz.localhost\r\n")
	for _, l := range lines {
		b.WriteString(l + "\r\n")
	}
	b.WriteString("Connection: close\r\n\r\n")
	if _, err := io.WriteString(conn, b.String()); err != nil {
		t.Fatal(err)
	}
	res, err := http.ReadResponse(bufio.NewReader(conn), nil)
	if err != nil {
		t.Fatalf("reading response: %v", err)
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	return res.StatusCode
}

// zzStartsWith reports whether Traefik starts an entry point that serves requests with the given flags.
// Start-up fails when loading the flags, the static-configuration validation the traefik command runs,
// creating the entry points, or starting the entry point reports an error or never serves a request.
func zzStartsWith(t *testing.T, flags ...string) bool {
	t.Helper()
	// The same starting point as the traefik command's configuration.
	cfg := &static.Configuration{
		Global:           &static.Global{},
		EntryPoints:      make(static.EntryPoints),
		Providers:        &static.Providers{},
		ServersTransport: &static.ServersTransport{MaxIdleConnsPerHost: 200},
	}
	args := append([]string{"--entryPoints.web.address=127.0.0.1:0"}, flags...)
	if err := flag.Decode(args, cfg); err != nil {
		return false
	}
	cfg.SetEffectiveConfiguration()
	if err := cfg.ValidateConfiguration(); err != nil {
		return false
	}
	eps, err := NewTCPEntryPoints(cfg.EntryPoints, nil)
	if err != nil {
		return false
	}
	ep, ok := eps["web"]
	if !ok {
		return false
	}
	router, err := tcprouter.NewRouter()
	if err != nil {
		t.Fatal(err)
	}
	backend := &zzBackend{}
	router.SetHTTPHandler(backend)
	go ep.Start(t.Context())
	ep.SwitchRouter(router)
	defer ep.Shutdown(t.Context())

	conn, err := net.Dial("tcp", ep.listener.Addr().String())
	if err != nil {
		return false
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(3 * time.Second))
	if _, err := io.WriteString(conn, "GET /zz HTTP/1.1\r\nHost: zz.localhost\r\nConnection: close\r\n\r\n"); err != nil {
		return false
	}
	res, err := http.ReadResponse(bufio.NewReader(conn), nil)
	if err != nil {
		return false
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	reached, _ := backend.take()
	return reached
}
