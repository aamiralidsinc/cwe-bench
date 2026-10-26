package functional

import (
	"testing"

	htests "github.com/fabiolb/fabio/htests_support"
)

// An ordinary gRPC call keeps being routed to the backend and metadata that
// the proxy does not derive keeps reaching the backend unchanged.
func TestFunc_GRPCCallAndOpaqueMetadata(t *testing.T) {
	backend, calls := htests.GRPCBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=grpc",
		"-registry.static.routes", htests.GRPCRoute(backend),
		"-proxy.header.clientip", "X-Client-IP",
		"-proxy.header.requestid", "X-Request-ID",
		"-proxy.header.tls", "X-Secure")

	if err := htests.GRPCCall(f.Addr(), "x-trace-tag", "keep-me"); err != nil {
		t.Fatalf("legitimate gRPC call failed: %v", err)
	}

	md := htests.RecvMetadata(t, calls)
	if got := md.Get("x-trace-tag"); len(got) != 1 || got[0] != "keep-me" {
		t.Errorf("backend saw x-trace-tag %v, want the client value %q", got, "keep-me")
	}
}
