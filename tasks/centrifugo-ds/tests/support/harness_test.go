package vtesting

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/centrifugal/centrifugo/v6/internal/client"
	"github.com/centrifugal/centrifugo/v6/internal/config"
	configtypes "github.com/centrifugal/centrifugo/v6/internal/configtypes"
	jwtverify "github.com/centrifugal/centrifugo/v6/internal/jwtverify"
	"github.com/centrifugal/centrifugo/v6/internal/metrics"
	proxy "github.com/centrifugal/centrifugo/v6/internal/proxy"
	proxyproto "github.com/centrifugal/centrifugo/v6/internal/proxyproto"
	"github.com/centrifugal/centrifugo/v6/internal/tools"

	"github.com/centrifugal/centrifuge"
	"github.com/prometheus/client_golang/prometheus"
	"google.golang.org/grpc"
	metadata "google.golang.org/grpc/metadata"
)

func TestMain(m *testing.M) {
	if err := metrics.Init(metrics.Config{Registerer: prometheus.NewRegistry()}); err != nil {
		panic(err)
	}
	os.Exit(m.Run())
}

// ---------- configuration ----------

func loadConfig(t *testing.T, body string) (config.Config, *config.Container) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "config.yaml")
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatalf("write config: %v", err)
	}
	cfg, _, err := config.GetConfig(nil, path)
	if err != nil {
		t.Fatalf("config: %v", err)
	}
	container, err := config.NewContainer(cfg)
	if err != nil {
		t.Fatalf("config container: %v", err)
	}
	return cfg, container
}

// connectProxyConfig returns the parsed default connect-proxy configuration.
func connectProxyConfig(cfg config.Config) configtypes.Proxy {
	return cfg.Client.Proxy.Connect.Proxy
}

// ---------- HTTP proxy backend ----------

type httpBackend struct {
	server *httptest.Server
	mu     sync.Mutex
	header http.Header
	calls  int
}

func newHTTPBackend(t *testing.T) *httpBackend {
	t.Helper()
	b := &httpBackend{}
	b.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		b.mu.Lock()
		b.header = req.Header.Clone()
		b.calls++
		b.mu.Unlock()
		_, _ = w.Write([]byte(`{"result":{"user":"42"}}`))
	}))
	t.Cleanup(b.server.Close)
	return b
}

func (b *httpBackend) received() http.Header {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.header
}

func (b *httpBackend) url(path string) string {
	return b.server.URL + path
}

// ---------- gRPC proxy backends ----------

type connectRecorder struct {
	proxyproto.UnimplementedCentrifugoProxyServer
	mu sync.Mutex
	md metadata.MD
}

func (s *connectRecorder) Connect(ctx context.Context, _ *proxyproto.ConnectRequest) (*proxyproto.ConnectResponse, error) {
	md, _ := metadata.FromIncomingContext(ctx)
	s.mu.Lock()
	s.md = md
	s.mu.Unlock()
	return &proxyproto.ConnectResponse{Result: &proxyproto.ConnectResult{User: "42"}}, nil
}

func (s *connectRecorder) metadata() metadata.MD {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.md
}

type streamRecorder struct {
	proxyproto.UnimplementedCentrifugoProxyServer
	md chan metadata.MD
}

func newStreamRecorder() *streamRecorder {
	return &streamRecorder{md: make(chan metadata.MD, 4)}
}

func (s *streamRecorder) SubscribeUnidirectional(_ *proxyproto.SubscribeRequest, stream grpc.ServerStreamingServer[proxyproto.StreamSubscribeResponse]) error {
	md, _ := metadata.FromIncomingContext(stream.Context())
	s.md <- md
	return stream.Send(&proxyproto.StreamSubscribeResponse{
		SubscribeResponse: &proxyproto.SubscribeResponse{Result: &proxyproto.SubscribeResult{}},
	})
}

func (s *streamRecorder) waitMetadata(t *testing.T, ctx context.Context) metadata.MD {
	t.Helper()
	select {
	case md := <-s.md:
		return md
	case <-ctx.Done():
		t.Fatalf("subscribe stream server did not receive the call: %v", ctx.Err())
		return nil
	}
}

// grpcTestConfig overrides a parsed proxy configuration so its gRPC client dials
// the in-process test server.
func grpcTestConfig(t *testing.T, p configtypes.Proxy, listener interface {
	Addr() net.Addr
	Dial() (net.Conn, error)
}) configtypes.Proxy {
	t.Helper()
	p.Endpoint = "passthrough:///" + listener.Addr().String()
	p.TestGrpcDialer = func(context.Context, string) (net.Conn, error) {
		return listener.Dial()
	}
	return p
}

func newGRPCConnectHandler(t *testing.T, srv proxyproto.CentrifugoProxyServer, p configtypes.Proxy, container *config.Container) proxy.ConnectingHandlerFunc {
	t.Helper()
	tc := tools.NewCommonGRPCProxyTestCase(context.Background(), srv)
	t.Cleanup(tc.Teardown)
	cp, err := proxy.GetConnectProxy("default", grpcTestConfig(t, p, tc.Listener))
	if err != nil {
		t.Fatalf("grpc connect proxy: %v", err)
	}
	return proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: cp}, container).Handle()
}

// ---------- client handler ----------

func newClientHandler(t *testing.T, container *config.Container) *client.Handler {
	t.Helper()
	verifier, err := jwtverify.NewTokenVerifierJWT(jwtverify.VerifierConfig{}, container)
	if err != nil {
		t.Fatalf("token verifier: %v", err)
	}
	node := tools.NodeWithMemoryEngine()
	t.Cleanup(func() { _ = node.Shutdown(context.Background()) })
	return client.NewHandler(node, container, verifier, nil, &client.ProxyMap{})
}

func testConnectEvent(headers map[string]string) centrifuge.ConnectEvent {
	return centrifuge.ConnectEvent{
		Transport: tools.NewTestTransport(),
		Headers:   headers,
	}
}

// ---------- extra proxy-config accessors ----------

func subscribeStreamConfig(cfg config.Config) configtypes.Proxy {
	return cfg.Channel.Proxy.SubscribeStream
}

func newGRPCTestCase(t *testing.T, srv proxyproto.CentrifugoProxyServer) *tools.CommonGRPCProxyTestCase {
	t.Helper()
	tc := tools.NewCommonGRPCProxyTestCase(context.Background(), srv)
	t.Cleanup(tc.Teardown)
	return tc
}
