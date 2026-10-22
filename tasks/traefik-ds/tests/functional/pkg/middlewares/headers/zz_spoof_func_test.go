package headers

import (
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

func zzExact(h http.Header, name string) []string {
	var out []string
	for hkey, values := range h {
		if strings.EqualFold(hkey, name) {
			out = append(out, values...)
		}
	}
	return out
}

func zzCheckUnrelated(t *testing.T, status int, b *zzBackend) http.Header {
	t.Helper()
	reached, header := b.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("legitimate request: status %d, reached backend %v", status, reached)
	}
	if got := zzExact(header, "X_Request_Tag"); !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("unrelated X_Request_Tag = %v, want it unchanged (headers %v)", got, header)
	}
	return header
}

// zzServeWith routes one request carrying the given header lines through the middleware.
func zzServeWith(t *testing.T, custom map[string]string, headers [][2]string) (int, *zzBackend) {
	t.Helper()
	backend := &zzBackend{}
	m, err := New(t.Context(), backend, dynamic.Headers{CustomRequestHeaders: custom}, "zz-headers")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewServer(m)
	t.Cleanup(srv.Close)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	for _, h := range headers {
		zzAddRaw(req, h[0], h[1])
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	return res.StatusCode, backend
}

var zzOtherHeaders = [][2]string{{"X_Request_Tag", "tag-1"}}

func TestFuncZZCustomRequestHeaderSetKeepsOtherHeaders(t *testing.T) {
	status, backend := zzServeWith(t, map[string]string{"X-Auth-User": "gateway", "X_Static_Tag": "s-1"}, zzOtherHeaders)
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"gateway"}) {
		t.Errorf("X-Auth-User = %v, want [gateway]", got)
	}
	if got := zzValuesAs(header, "X_Static_Tag"); !reflect.DeepEqual(got, []string{"s-1"}) {
		t.Errorf("configured X_Static_Tag = %v, want [s-1]", got)
	}
}

func TestFuncZZCustomRequestHeaderRemoveKeepsOtherHeaders(t *testing.T) {
	status, backend := zzServeWith(t, map[string]string{"X-Auth-User": ""}, append(zzOtherHeaders, [2]string{"X-Auth-User", "alice"}))
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X-Auth-User"); len(got) != 0 {
		t.Errorf("X-Auth-User = %v, want removed", got)
	}
}

// A header configured with underscores is set, and the other underscore headers that are not
// configured are forwarded unchanged.
func TestFuncZZCustomRequestHeaderConfiguredUnderscore(t *testing.T) {
	status, backend := zzServeWith(t, map[string]string{"X_Static_Tag": "s-1"}, zzOtherHeaders)
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X_Static_Tag"); !reflect.DeepEqual(got, []string{"s-1"}) {
		t.Errorf("configured X_Static_Tag = %v, want [s-1] (headers %v)", got, header)
	}
}

// Removing a header configured with underscores leaves the other headers alone.
func TestFuncZZCustomRequestHeaderRemoveConfiguredUnderscore(t *testing.T) {
	status, backend := zzServeWith(t, map[string]string{"X_Auth_User": ""}, append(zzOtherHeaders, [2]string{"X_Auth_User", "alice"}))
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X_Auth_User"); len(got) != 0 {
		t.Errorf("X_Auth_User = %v, want removed", got)
	}
}
