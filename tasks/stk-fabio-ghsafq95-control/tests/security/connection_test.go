package security

import (
	"strings"
	"testing"

	htests "github.com/fabiolb/fabio/htests_support"
)

// A client must not be able to make the proxy drop a forwarding header it
// derives by declaring that header hop-by-hop.
func TestSec_ConnectionTokenDoesNotRemoveRealIP(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close, X-Real-Ip"))

	h := htests.RecvHeader(t, headers)
	if !htests.IsLoopbackValue(h.Get("X-Real-Ip")) {
		t.Errorf("backend saw X-Real-Ip %q, want the value derived from the client address", h.Get("X-Real-Ip"))
	}
}

func TestSec_ConnectionTokenDoesNotRemoveForwardedHost(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close, X-Forwarded-Host"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Forwarded-Host"); got != "example.com" {
		t.Errorf("backend saw X-Forwarded-Host %q, want %q", got, "example.com")
	}
}

func TestSec_ConnectionTokenDoesNotRemoveForwardedProto(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close, X-Forwarded-Proto"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Forwarded-Proto"); got != "http" {
		t.Errorf("backend saw X-Forwarded-Proto %q, want %q", got, "http")
	}
}

func TestSec_ConnectionTokenDoesNotRemoveForwarded(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close, Forwarded"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("Forwarded"); !strings.Contains(got, "for=127.0.0.1") {
		t.Errorf("backend saw Forwarded %q, want the value derived from the client address", got)
	}
}

func TestSec_ConnectionDeclarationAcrossLines(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL))

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"Connection: X-Forwarded-Port"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Forwarded-Port"); got != "80" {
		t.Errorf("backend saw X-Forwarded-Port %q, want %q", got, "80")
	}
}
