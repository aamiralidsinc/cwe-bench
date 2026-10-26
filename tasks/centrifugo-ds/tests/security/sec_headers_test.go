package vtesting

import (
	"context"
	"fmt"
	"testing"
	"time"

	clientcontext "github.com/centrifugal/centrifugo/v6/internal/clientcontext"
	proxy "github.com/centrifugal/centrifugo/v6/internal/proxy"
	proxyproto "github.com/centrifugal/centrifugo/v6/internal/proxyproto"

	metadata "google.golang.org/grpc/metadata"
)

// A value the client supplies through header emulation must never reach a proxy
// backend under a name the proxy configuration reserves for transport headers.

func TestSec_HTTPProxy_EmulatedDoesNotFillTransportHeader(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-forwarded-for]
      emulated_headers: []
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := clientcontext.SetEmulatedHeadersToContext(context.Background(), map[string]string{
		"X-Forwarded-For": "203.0.113.9",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := backend.received().Get("X-Forwarded-For"); got != "" {
		t.Fatalf("client emulation supplied a value for a header reserved for transport data: %q", got)
	}
}

func TestSec_GRPCProxy_EmulatedDoesNotFillTransportHeader(t *testing.T) {
	srv := &connectRecorder{}
	cfg, container := loadConfig(t, `
client:
  proxy:
    connect:
      enabled: true
      endpoint: passthrough:///placeholder
      timeout: 5s
      http_headers: [x-forwarded-for]
      emulated_headers: []
`)
	handler := newGRPCConnectHandler(t, srv, connectProxyConfig(cfg), container)

	ctx := clientcontext.SetEmulatedHeadersToContext(context.Background(), map[string]string{
		"X-Forwarded-For": "203.0.113.9",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if vals := srv.metadata().Get("x-forwarded-for"); len(vals) != 0 {
		t.Fatalf("client emulation supplied a value for transport metadata: %q", vals)
	}
}

func TestSec_ConnectPath_EmulatedDoesNotFillTransportHeader(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-forwarded-for]
      emulated_headers: []
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	proxyHandler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	handler := newClientHandler(t, container)
	_, err = handler.OnClientConnecting(context.Background(), testConnectEvent(map[string]string{
		"X-Forwarded-For": "203.0.113.9",
	}), proxyHandler, false)
	if err != nil {
		t.Fatalf("connect failed: %v", err)
	}
	if got := backend.received().Get("X-Forwarded-For"); got != "" {
		t.Fatalf("client emulation supplied a value for a header reserved for transport data: %q", got)
	}
}

func TestSec_TransportValueWinsOverEmulated(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-user-id]
      grpc_metadata: [x-user-id]
      emulated_headers: [x-user-id]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := context.Background()
	ctx = metadata.NewIncomingContext(ctx, metadata.MD{"x-user-id": []string{"transport-value"}})
	ctx = clientcontext.SetEmulatedHeadersToContext(ctx, map[string]string{
		"X-User-Id": "emulated-value",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	values := backend.received().Values("X-User-Id")
	if len(values) != 1 || values[0] != "transport-value" {
		t.Fatalf("backend observed %q for a name supplied by both transport and emulation; the transport value must be the only one", values)
	}
}

func TestSec_SubscribeStream_EmulatedDoesNotFillTransportHeader(t *testing.T) {
	srv := newStreamRecorder()
	tc := newGRPCTestCase(t, srv)
	cfg, _ := loadConfig(t, `
channel:
  proxy:
    subscribe_stream:
      endpoint: passthrough:///placeholder
      timeout: 5s
      http_headers: [x-forwarded-for]
`)

	p, err := proxy.NewSubscribeStreamProxy("default", grpcTestConfig(t, subscribeStreamConfig(cfg), tc.Listener))
	if err != nil {
		t.Fatalf("subscribe stream proxy: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	ctx = clientcontext.SetEmulatedHeadersToContext(ctx, map[string]string{
		"X-Forwarded-For": "203.0.113.9",
	})
	stream, err := p.SubscribeUnidirectional(ctx, &proxyproto.SubscribeRequest{Client: "c1", Channel: "ch"})
	if err != nil {
		t.Fatalf("subscribe stream call failed: %v", err)
	}
	if _, err := stream.Recv(); err != nil {
		t.Fatalf("subscribe stream receive failed: %v", err)
	}
	md := srv.waitMetadata(t, ctx)
	if vals := md.Get("x-forwarded-for"); len(vals) != 0 {
		t.Fatalf("client emulation supplied a value for transport metadata: %q", vals)
	}
}
