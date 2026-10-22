package headers

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

var zzAliasSpellings = []string{"X_Auth_User", "X_Auth-User", "X-Auth_User"}

const zzSpoof = "zz-spoofed-admin"

func zzServe(t *testing.T, custom map[string]string, spelling string) (int, *zzBackend) {
	t.Helper()
	backend := &zzBackend{}
	m, err := New(t.Context(), backend, dynamic.Headers{CustomRequestHeaders: custom}, "zz-headers")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	zzAddRaw(req, spelling, zzSpoof)
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	return res.StatusCode, backend
}

// A request header the operator configures to be removed must not reach the backend under
// another spelling the backend reads as the same header.
func TestSecZZCustomRequestHeaderRemovedAlias(t *testing.T) {
	for _, spelling := range zzAliasSpellings {
		t.Run("client "+spelling, func(t *testing.T) {
			status, backend := zzServe(t, map[string]string{"X-Auth-User": ""}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
	for _, spelling := range []string{"X_Forwarded_For", "X-Forwarded_For"} {
		t.Run("X-Forwarded-For client "+spelling, func(t *testing.T) {
			status, backend := zzServe(t, map[string]string{"X-Forwarded-For": ""}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Forwarded-For", zzSpoof)
		})
	}
}

// Same when the operator wrote the removed header name with underscores.
func TestSecZZCustomRequestHeaderRemovedConfiguredUnderscore(t *testing.T) {
	for _, spelling := range []string{"X-Auth-User", "X_Auth-User", "X-Auth_User", "x-auth-user"} {
		t.Run("client "+spelling, func(t *testing.T) {
			status, backend := zzServe(t, map[string]string{"X_Auth_User": ""}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

// A request header the operator configures to a fixed value must not be accompanied by a
// client-supplied spelling of the same header.
func TestSecZZCustomRequestHeaderSetAlias(t *testing.T) {
	for _, spelling := range zzAliasSpellings {
		t.Run("client "+spelling, func(t *testing.T) {
			status, backend := zzServe(t, map[string]string{"X-Auth-User": "gateway"}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

// Same when the operator wrote the set header name with underscores.
func TestSecZZCustomRequestHeaderSetConfiguredUnderscore(t *testing.T) {
	for _, spelling := range []string{"X-Auth-User", "X_Auth-User", "X-Auth_User", "x-auth-user"} {
		t.Run("client "+spelling, func(t *testing.T) {
			status, backend := zzServe(t, map[string]string{"X_Auth_User": "gateway"}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}
