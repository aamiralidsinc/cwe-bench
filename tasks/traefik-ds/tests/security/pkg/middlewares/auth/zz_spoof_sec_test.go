package auth

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

// Client spellings of the X-Auth-User header that a backend reading '_' as '-' and ignoring case
// treats as X-Auth-User itself.
var zzAliasSpellings = []string{"X_Auth_User", "X_Auth-User", "X-Auth_User", "x_auth_user"}

const zzSpoof = "zz-spoofed-admin"

func zzDo(t *testing.T, client interface {
	Do(*http.Request) (*http.Response, error)
}, req *http.Request,
) int {
	t.Helper()
	res, err := client.Do(req)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	return res.StatusCode
}

// An authenticated user must not be able to choose the identity the backend reads from the
// user header that basic authentication sets.
func TestSecZZBasicAuthUserHeaderAlias(t *testing.T) {
	fields := map[string][]string{
		"X-Auth-User": zzAliasSpellings,
		"x-auth-user": zzAliasSpellings,
		// A configured spelling with underscores already matches two of the client spellings, so
		// only the mixed ones show the defect; the canonical case is covered functionally.
		"X_Auth_User": {"X_Auth-User", "X-Auth_User"},
	}
	for field, spellings := range fields {
		for _, spelling := range spellings {
			t.Run("field "+field+" client "+spelling, func(t *testing.T) {
				backend := &zzBackend{}
				m, err := NewBasic(t.Context(), backend, dynamic.BasicAuth{
					Users:       []string{"test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"},
					HeaderField: field,
				}, "zz-basic")
				if err != nil {
					t.Fatal(err)
				}
				srv := httptest.NewServer(m)
				t.Cleanup(srv.Close)

				req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
				req.SetBasicAuth("test", "test")
				zzAddRaw(req, spelling, zzSpoof)

				status := zzDo(t, http.DefaultClient, req)
				zzAssertNotSpoofed(t, status, backend, field, zzSpoof)
			})
		}
	}
}

// Same property for the user header that digest authentication sets.
func TestSecZZDigestAuthUserHeaderAlias(t *testing.T) {
	for _, spelling := range zzAliasSpellings[:3] {
		t.Run("client "+spelling, func(t *testing.T) {
			backend := &zzBackend{}
			m, err := NewDigest(t.Context(), backend, dynamic.DigestAuth{
				Users:       []string{"test:traefik:a2688e031edb4be6a3797f3882655c05"},
				HeaderField: "X-Auth-User",
			}, "zz-digest")
			if err != nil {
				t.Fatal(err)
			}
			srv := httptest.NewServer(m)
			t.Cleanup(srv.Close)

			req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
			zzAddRaw(req, spelling, zzSpoof)

			status := zzDo(t, newDigestRequest("test", "test", http.DefaultClient), req)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

func zzAuthServer(t *testing.T, respond http.Header) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, _ *http.Request) {
		for k, v := range respond {
			rw.Header()[k] = v
		}
		rw.WriteHeader(http.StatusOK)
	}))
	t.Cleanup(srv.Close)
	return srv
}

// Headers that forward authentication copies from the authentication service (listed by name)
// must not be accompanied by a client-supplied spelling of the same header.
func TestSecZZForwardAuthResponseHeaderAlias(t *testing.T) {
	responses := map[string]http.Header{
		"auth sets user":      {"X-Auth-User": {"alice"}},
		"auth sets no user":   {},
		"auth sets other hdr": {"X-Auth-Group": {"staff"}},
	}
	for rname, respond := range responses {
		for _, spelling := range zzAliasSpellings[:3] {
			t.Run(rname+" client "+spelling, func(t *testing.T) {
				authSrv := zzAuthServer(t, respond)
				backend := &zzBackend{}
				m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
					Address:             authSrv.URL,
					AuthResponseHeaders: []string{"X-Auth-User", "X-Auth-Group"},
				}, "zz-forward")
				if err != nil {
					t.Fatal(err)
				}
				srv := httptest.NewServer(m)
				t.Cleanup(srv.Close)

				req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
				zzAddRaw(req, spelling, zzSpoof)

				status := zzDo(t, http.DefaultClient, req)
				zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
			})
		}
	}
}

// Same property when the operator configured the copied header name with underscores: a client
// spelling with dashes is the same header for the backend.
func TestSecZZForwardAuthResponseHeaderConfiguredUnderscore(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X_Auth_User": {"alice"}})
	for _, spelling := range []string{"X-Auth-User", "X-Auth_User", "x-auth-user"} {
		t.Run("client "+spelling, func(t *testing.T) {
			backend := &zzBackend{}
			m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
				Address:             authSrv.URL,
				AuthResponseHeaders: []string{"X_Auth_User"},
			}, "zz-forward-underscore")
			if err != nil {
				t.Fatal(err)
			}
			srv := httptest.NewServer(m)
			t.Cleanup(srv.Close)

			req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
			zzAddRaw(req, spelling, zzSpoof)

			status := zzDo(t, http.DefaultClient, req)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

// Same property when the copied headers are selected by a regular expression written with dashes.
func TestSecZZForwardAuthResponseHeaderRegexAlias(t *testing.T) {
	for _, spelling := range zzAliasSpellings[:3] {
		t.Run("client "+spelling, func(t *testing.T) {
			authSrv := zzAuthServer(t, http.Header{"X-Auth-User": {"alice"}})
			backend := &zzBackend{}
			m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
				Address:                  authSrv.URL,
				AuthResponseHeadersRegex: "^X-Auth-",
			}, "zz-forward-regex")
			if err != nil {
				t.Fatal(err)
			}
			srv := httptest.NewServer(m)
			t.Cleanup(srv.Close)

			req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
			zzAddRaw(req, spelling, zzSpoof)

			status := zzDo(t, http.DefaultClient, req)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

// Same property when the pattern is written with underscores, as an operator reading the
// backend's configuration would write it: the dashed client spelling is the same header.
func TestSecZZForwardAuthResponseHeaderRegexConfiguredUnderscore(t *testing.T) {
	for _, spelling := range []string{"X-Auth-User", "X-Auth_User", "X_Auth-User", "x-auth-user"} {
		t.Run("client "+spelling, func(t *testing.T) {
			authSrv := zzAuthServer(t, http.Header{"X_Auth_User": {"alice"}})
			backend := &zzBackend{}
			m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
				Address:                  authSrv.URL,
				AuthResponseHeadersRegex: "^X_Auth_",
			}, "zz-forward-regex-underscore")
			if err != nil {
				t.Fatal(err)
			}
			srv := httptest.NewServer(m)
			t.Cleanup(srv.Close)

			req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
			zzAddRaw(req, spelling, zzSpoof)

			status := zzDo(t, http.DefaultClient, req)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}

// The client spelling that differs from the copied header only by mixing '_' and '-' must not
// survive either: the tree's case-only alias filter does not fold the two characters.
func TestSecZZForwardAuthResponseHeaderMixedSpelling(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X-Auth-User": {"alice"}})
	for _, spelling := range []string{"X_Auth-User", "X-Auth_User"} {
		t.Run("client "+spelling, func(t *testing.T) {
			backend := &zzBackend{}
			m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
				Address:             authSrv.URL,
				AuthResponseHeaders: []string{"X-Auth-User"},
			}, "zz-forward-mixed")
			if err != nil {
				t.Fatal(err)
			}
			srv := httptest.NewServer(m)
			t.Cleanup(srv.Close)

			req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
			zzAddRaw(req, spelling, zzSpoof)

			status := zzDo(t, http.DefaultClient, req)
			zzAssertNotSpoofed(t, status, backend, "X-Auth-User", zzSpoof)
		})
	}
}
