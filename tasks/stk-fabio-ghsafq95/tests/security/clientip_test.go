package security

import (
	"testing"

	htests "github.com/fabiolb/fabio/htests_support"
)

// When the operator designates a header to carry the client address, a
// client-supplied value for that header must not replace the derived value.
func TestSec_DesignatedClientIPHeaderIsFabios(t *testing.T) {
	be, headers := htests.HTTPBackend(t)
	f := htests.StartFabio(t, htests.FreeAddr(t)+";proto=http",
		"-registry.static.routes", htests.HTTPRoute(be.URL),
		"-proxy.header.clientip", "X-Real-Ip")

	htests.RawRequest(t, f.Addr(), htests.BuildRequest("GET", "/x", "example.com",
		"Connection: close",
		"X-Real-Ip: 9.9.9.9"))

	h := htests.RecvHeader(t, headers)
	if got := h.Get("X-Real-Ip"); !htests.IsLoopbackValue(got) {
		t.Errorf("backend saw X-Real-Ip %q, want the value derived from the client address", got)
	}
}
