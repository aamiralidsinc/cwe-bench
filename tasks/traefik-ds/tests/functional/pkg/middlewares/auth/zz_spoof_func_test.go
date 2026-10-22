package auth

import (
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

// zzExact returns the values received under name, ignoring only letter case.
func zzExact(h http.Header, name string) []string {
	var out []string
	for hkey, values := range h {
		if strings.EqualFold(hkey, name) {
			out = append(out, values...)
		}
	}
	return out
}

// zzUnrelated are client headers that no feature under test sets or removes; they must arrive unchanged.
var zzUnrelated = map[string]string{
	"X_Request_Tag":  "t-1",
	"X_Auth_Role":    "viewer",
	"X-Auth-User-Id": "7",
}

func zzAddUnrelated(req *http.Request) {
	for k, v := range zzUnrelated {
		zzAddRaw(req, k, v)
	}
}

func zzCheckRouted(t *testing.T, status int, b *zzBackend) http.Header {
	t.Helper()
	reached, header := b.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("legitimate request: status %d, reached backend %v", status, reached)
	}
	for k, v := range zzUnrelated {
		if got := zzExact(header, k); !reflect.DeepEqual(got, []string{v}) {
			t.Errorf("unrelated header %s = %v, want [%s] unchanged (headers %v)", k, got, v, header)
		}
	}
	return header
}

func TestFuncZZBasicAuthUserHeaderAndOtherHeaders(t *testing.T) {
	backend := &zzBackend{}
	m, err := NewBasic(t.Context(), backend, dynamic.BasicAuth{
		Users:       []string{"test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"},
		HeaderField: "X-Auth-User",
	}, "zz-basic")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	req.SetBasicAuth("test", "test")
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"test"}) {
		t.Errorf("user header = %v, want [test]", got)
	}
}

func TestFuncZZBasicAuthWithoutUserHeaderForwardsUnderscoreHeaders(t *testing.T) {
	backend := &zzBackend{}
	m, err := NewBasic(t.Context(), backend, dynamic.BasicAuth{
		Users: []string{"test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"},
	}, "zz-basic")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	req.SetBasicAuth("test", "test")
	zzAddRaw(req, "X_Auth_User", "carol")
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzExact(header, "X_Auth_User"); !reflect.DeepEqual(got, []string{"carol"}) {
		t.Errorf("X_Auth_User = %v, want [carol]: no feature manages it here", got)
	}
}

// A user header configured with underscores keeps its configured spelling and its value.
func TestFuncZZBasicAuthUnderscoreUserHeader(t *testing.T) {
	backend := &zzBackend{}
	m, err := NewBasic(t.Context(), backend, dynamic.BasicAuth{
		Users:       []string{"test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"},
		HeaderField: "X_Auth_User",
	}, "zz-basic-underscore")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	req.SetBasicAuth("test", "test")
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := header["X_Auth_User"]; !reflect.DeepEqual(got, []string{"test"}) {
		t.Errorf("configured X_Auth_User = %v, want [test] (headers %v)", got, header)
	}
}

func TestFuncZZDigestAuthUserHeaderAndOtherHeaders(t *testing.T) {
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
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, newDigestRequest("test", "test", http.DefaultClient), req), backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"test"}) {
		t.Errorf("user header = %v, want [test]", got)
	}
}

func TestFuncZZForwardAuthResponseHeadersAndOtherHeaders(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X-Auth-User": {"alice"}, "X-Auth-Group": {"staff", "ops"}})
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
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"alice"}) {
		t.Errorf("X-Auth-User = %v, want [alice]", got)
	}
	if got := zzValuesAs(header, "X-Auth-Group"); !reflect.DeepEqual(got, []string{"staff", "ops"}) {
		t.Errorf("X-Auth-Group = %v, want [staff ops]", got)
	}
}

// A copied header configured with underscores still carries the authentication service's value.
func TestFuncZZForwardAuthResponseHeadersConfiguredUnderscore(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X_Auth_User": {"alice"}})
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
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"alice"}) {
		t.Errorf("X-Auth-User = %v, want [alice]", got)
	}
}

func TestFuncZZForwardAuthResponseHeadersRegexAndOtherHeaders(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X-Auth-User": {"alice"}})
	backend := &zzBackend{}
	m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{
		Address:                  authSrv.URL,
		AuthResponseHeadersRegex: "^X-Auth-User$",
	}, "zz-forward-regex")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"alice"}) {
		t.Errorf("X-Auth-User = %v, want [alice]", got)
	}
}

func TestFuncZZForwardAuthWithoutResponseHeadersForwardsUnderscoreHeaders(t *testing.T) {
	authSrv := zzAuthServer(t, http.Header{"X-Auth-User": {"alice"}})
	backend := &zzBackend{}
	m, err := NewForward(t.Context(), backend, dynamic.ForwardAuth{Address: authSrv.URL}, "zz-forward")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	zzAddRaw(req, "X_Auth_User", "carol")
	zzAddUnrelated(req)
	header := zzCheckRouted(t, zzDo(t, http.DefaultClient, req), backend)
	if got := zzExact(header, "X_Auth_User"); !reflect.DeepEqual(got, []string{"carol"}) {
		t.Errorf("X_Auth_User = %v, want [carol]: no feature manages it here", got)
	}
}
