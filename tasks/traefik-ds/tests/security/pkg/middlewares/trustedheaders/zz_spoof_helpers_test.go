package trustedheaders

import (
	"net/http"
	"strings"
	"sync"
	"testing"
)

// zzBackend records what reached the backend behind the middleware under test.
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

func (b *zzBackend) seen() (bool, http.Header) {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.reached, b.header
}

// zzSameName reports whether a backend that ignores case and reads '_' as '-' sees both names as one header.
func zzSameName(a, b string) bool {
	return strings.EqualFold(strings.ReplaceAll(a, "_", "-"), strings.ReplaceAll(b, "_", "-"))
}

// zzValuesAs returns every value the backend received under any spelling of name.
func zzValuesAs(h http.Header, name string) []string {
	var out []string
	for key, values := range h {
		if zzSameName(key, name) {
			out = append(out, values...)
		}
	}
	return out
}

// zzAddRaw adds a header with its name exactly as given (the client writes it as is on the wire).
func zzAddRaw(req *http.Request, name, value string) {
	req.Header[name] = append(req.Header[name], value)
}

// zzAssertNotSpoofed: the attack is blocked when the request was refused with a client error before
// reaching the backend, or when the backend received no value carrying the marker under any spelling of name.
func zzAssertNotSpoofed(t *testing.T, status int, b *zzBackend, name, marker string) {
	t.Helper()
	reached, header := b.seen()
	if !reached {
		if status < 400 || status > 499 {
			t.Fatalf("request did not reach the backend but got status %d (want a client error)", status)
		}
		return
	}
	for _, v := range zzValuesAs(header, name) {
		if strings.Contains(v, marker) {
			t.Fatalf("backend received the client-supplied value %q as %s (headers: %v)", v, name, header)
		}
	}
}
