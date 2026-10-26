package vtesting

import (
	"context"
	"fmt"
	"net/http"
	"testing"
	"time"

	clientcontext "github.com/centrifugal/centrifugo/v6/internal/clientcontext"
	middleware "github.com/centrifugal/centrifugo/v6/internal/middleware"
	proxy "github.com/centrifugal/centrifugo/v6/internal/proxy"
	proxyproto "github.com/centrifugal/centrifugo/v6/internal/proxyproto"

	metadata "google.golang.org/grpc/metadata"
)

// Ordinary proxy header handling must keep working: transport headers, static
// values and client values the configuration designates for emulation.

func TestFunc_DualSourceEmulatedFallback(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [authorization]
      emulated_headers: [authorization]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := clientcontext.SetEmulatedHeadersToContext(context.Background(), map[string]string{
		"Authorization": "Bearer from-emulation",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := backend.received().Get("Authorization"); got != "Bearer from-emulation" {
		t.Fatalf("authorization header designated for emulation was not forwarded: %q", got)
	}
}

func TestFunc_DualSourceTransportValueWins(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [authorization]
      emulated_headers: [authorization]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := middleware.SetHeadersToContext(context.Background(), http.Header{
		"Authorization": []string{"Bearer from-transport"},
	})
	ctx = clientcontext.SetEmulatedHeadersToContext(ctx, map[string]string{
		"Authorization": "Bearer from-emulation",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := backend.received().Values("Authorization"); len(got) != 1 || got[0] != "Bearer from-transport" {
		t.Fatalf("transport value must win over the emulated fallback, backend observed %q", got)
	}
}

func TestFunc_TransportOnlyHeaderForwarded(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-real-ip]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := middleware.SetHeadersToContext(context.Background(), http.Header{
		"X-Real-Ip": []string{"198.51.100.7"},
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := backend.received().Get("X-Real-Ip"); got != "198.51.100.7" {
		t.Fatalf("transport header was not forwarded: %q", got)
	}
}

func TestFunc_StaticHeadersStillApplied(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-static]
      http:
        static_headers:
          x-static: static-value
          x-other-static: other-value
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := middleware.SetHeadersToContext(context.Background(), http.Header{
		"X-Static": []string{"client-value"},
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	headers := backend.received()
	if got := headers.Get("X-Static"); got != "client-value" {
		t.Fatalf("allow-listed transport header should override a static header, got %q", got)
	}
	if got := headers.Get("X-Other-Static"); got != "other-value" {
		t.Fatalf("static header that no client value names should be preserved, got %q", got)
	}
}

func TestFunc_GRPCTransportMetadataForwarded(t *testing.T) {
	srv := &connectRecorder{}
	cfg, container := loadConfig(t, `
client:
  proxy:
    connect:
      enabled: true
      endpoint: passthrough:///placeholder
      timeout: 5s
      grpc_metadata: [x-meta]
`)
	handler := newGRPCConnectHandler(t, srv, connectProxyConfig(cfg), container)

	ctx := metadata.NewIncomingContext(context.Background(), metadata.MD{
		"x-meta": []string{"meta-value"},
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := srv.metadata().Get("x-meta"); len(got) != 1 || got[0] != "meta-value" {
		t.Fatalf("transport metadata was not forwarded: %q", got)
	}
}

func TestFunc_GRPCStaticMetadataStillApplied(t *testing.T) {
	srv := &connectRecorder{}
	cfg, container := loadConfig(t, `
client:
  proxy:
    connect:
      enabled: true
      endpoint: passthrough:///placeholder
      timeout: 5s
      grpc:
        static_metadata:
          x-static: static-value
`)
	handler := newGRPCConnectHandler(t, srv, connectProxyConfig(cfg), container)
	if _, _, err := handler(context.Background(), testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := srv.metadata().Get("x-static"); len(got) != 1 || got[0] != "static-value" {
		t.Fatalf("static metadata was not applied: %q", got)
	}
}

func TestFunc_UnlistedEmulatedHeaderNotForwarded(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [x-real-ip]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	handler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	ctx := clientcontext.SetEmulatedHeadersToContext(context.Background(), map[string]string{
		"X-Unlisted": "value",
	})
	if _, _, err := handler(ctx, testConnectEvent(nil)); err != nil {
		t.Fatalf("connect proxy call failed: %v", err)
	}
	if got := backend.received().Get("X-Unlisted"); got != "" {
		t.Fatalf("header listed in neither allow list was forwarded: %q", got)
	}
}

func TestFunc_ConnectStillSucceeds(t *testing.T) {
	backend := newHTTPBackend(t)
	cfg, container := loadConfig(t, fmt.Sprintf(`
client:
  proxy:
    connect:
      enabled: true
      endpoint: %s
      timeout: 5s
      http_headers: [authorization]
      emulated_headers: [authorization]
`, backend.url("/proxy")))

	connect, err := proxy.GetConnectProxy("default", connectProxyConfig(cfg))
	if err != nil {
		t.Fatalf("connect proxy: %v", err)
	}
	proxyHandler := proxy.NewConnectHandler(proxy.ConnectHandlerConfig{Proxy: connect}, container).Handle()

	handler := newClientHandler(t, container)
	reply, err := handler.OnClientConnecting(context.Background(), testConnectEvent(map[string]string{
		"Authorization": "Bearer from-emulation",
	}), proxyHandler, false)
	if err != nil {
		t.Fatalf("ordinary connect failed: %v", err)
	}
	if reply.Credentials == nil || reply.Credentials.UserID != "42" {
		t.Fatalf("connect reply did not carry the backend credentials: %+v", reply.Credentials)
	}
}

func TestFunc_SubscribeStreamTransportMetadataForwarded(t *testing.T) {
	srv := newStreamRecorder()
	tc := newGRPCTestCase(t, srv)
	cfg, _ := loadConfig(t, `
channel:
  proxy:
    subscribe_stream:
      endpoint: passthrough:///placeholder
      timeout: 5s
      grpc_metadata: [x-meta]
`)
	p, err := proxy.NewSubscribeStreamProxy("default", grpcTestConfig(t, subscribeStreamConfig(cfg), tc.Listener))
	if err != nil {
		t.Fatalf("subscribe stream proxy: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	ctx = metadata.NewIncomingContext(ctx, metadata.MD{"x-meta": []string{"meta-value"}})
	stream, err := p.SubscribeUnidirectional(ctx, &proxyproto.SubscribeRequest{Client: "c1", Channel: "ch"})
	if err != nil {
		t.Fatalf("subscribe stream call failed: %v", err)
	}
	if _, err := stream.Recv(); err != nil {
		t.Fatalf("subscribe stream receive failed: %v", err)
	}
	md := srv.waitMetadata(t, ctx)
	if got := md.Get("x-meta"); len(got) != 1 || got[0] != "meta-value" {
		t.Fatalf("transport metadata was not forwarded on the subscribe stream: %q", got)
	}
}

func TestFunc_SubscribeStreamStaticMetadataStillApplied(t *testing.T) {
	srv := newStreamRecorder()
	tc := newGRPCTestCase(t, srv)
	cfg, _ := loadConfig(t, `
channel:
  proxy:
    subscribe_stream:
      endpoint: passthrough:///placeholder
      timeout: 5s
      grpc:
        static_metadata:
          x-static: static-value
`)
	p, err := proxy.NewSubscribeStreamProxy("default", grpcTestConfig(t, subscribeStreamConfig(cfg), tc.Listener))
	if err != nil {
		t.Fatalf("subscribe stream proxy: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	stream, err := p.SubscribeUnidirectional(ctx, &proxyproto.SubscribeRequest{Client: "c1", Channel: "ch"})
	if err != nil {
		t.Fatalf("subscribe stream call failed: %v", err)
	}
	if _, err := stream.Recv(); err != nil {
		t.Fatalf("subscribe stream receive failed: %v", err)
	}
	md := srv.waitMetadata(t, ctx)
	if got := md.Get("x-static"); len(got) != 1 || got[0] != "static-value" {
		t.Fatalf("static metadata was not applied on the subscribe stream: %q", got)
	}
}
