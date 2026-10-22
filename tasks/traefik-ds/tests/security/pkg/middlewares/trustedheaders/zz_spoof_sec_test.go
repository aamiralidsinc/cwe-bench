package trustedheaders

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

const zzSpoof = "zz-spoofed-admin"

// zzServeUntrusted routes one request whose ClientAddr is not in TrustedIPs through the
// middleware, carrying the given spelling of header.
func zzServeUntrusted(t *testing.T, reserved []string, spelling string) (int, *zzBackend) {
	t.Helper()
	backend := &zzBackend{}
	m, err := New(t.Context(), backend, dynamic.TrustedHeaders{
		Headers:    reserved,
		TrustedIPs: []string{"10.0.0.0/8"},
	}, "zz-trusted-headers")
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
	_ = res.Body.Close()
	return res.StatusCode, backend
}

// A header reserved for the trusted upstream must not reach the backend from an untrusted client
// under any spelling the backend reads as the same header.
func TestSecZZTrustedHeadersReservedHeaderAlias(t *testing.T) {
	for _, spelling := range []string{"X_Auth_User", "X_Auth-User", "X-Auth_User", "x_auth_user"} {
		t.Run("user header client "+spelling, func(t *testing.T) {
			status, backend := zzServeUntrusted(t, []string{"X-Auth-User", "X-Auth-Group"}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}

	// The same property for a second reserved name of the same configuration.
	for _, spelling := range []string{"X_Auth_Group", "X-Auth_Group"} {
		t.Run("group header client "+spelling, func(t *testing.T) {
			status, backend := zzServeUntrusted(t, []string{"X-Auth-User", "X-Auth-Group"}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-Group", zzSpoof)
		})
	}
}

// A reserved name configured with underscores must also keep out its dashed spelling.
func TestSecZZTrustedHeadersReservedHeaderConfiguredUnderscore(t *testing.T) {
	for _, spelling := range []string{"X-Auth-User", "X-Auth_User", "X_Auth-User", "x-auth-user"} {
		t.Run("client "+spelling, func(t *testing.T) {
			status, backend := zzServeUntrusted(t, []string{"X_Auth_User"}, spelling)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}
