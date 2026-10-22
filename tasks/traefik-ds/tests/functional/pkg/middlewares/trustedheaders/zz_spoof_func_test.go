package trustedheaders

import (
	"net/http"
	"net/http/httptest"
	"reflect"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

// zzRequest routes one request carrying the given header lines through the middleware.
func zzRequest(t *testing.T, config dynamic.TrustedHeaders, headers [][2]string) (int, *zzBackend) {
	t.Helper()
	backend := &zzBackend{}
	m, err := New(t.Context(), backend, config, "zz-trusted-headers")
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
	_ = res.Body.Close()
	return res.StatusCode, backend
}

// A client in the trusted range still supplies the reserved headers, in every spelling, and
// unrelated headers are untouched.
func TestFuncZZTrustedHeadersTrustedPeerForwarded(t *testing.T) {
	config := dynamic.TrustedHeaders{
		Headers:    []string{"X-Auth-User", "X-Auth-Group"},
		TrustedIPs: []string{"127.0.0.1/32"},
	}
	headers := [][2]string{
		{"X-Auth-User", "alice"},
		{"X_Auth_Group", "staff"},
		{"X-Request_Tag", "tag-1"},
	}
	status, backend := zzRequest(t, config, headers)
	reached, received := backend.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("trusted request: status %d, reached backend %v", status, reached)
	}
	if got := zzValuesAs(received, "X-Auth-User"); !reflect.DeepEqual(got, []string{"alice"}) {
		t.Errorf("X-Auth-User = %v, want [alice]", got)
	}
	if got := zzValuesAs(received, "X-Auth-Group"); !reflect.DeepEqual(got, []string{"staff"}) {
		t.Errorf("X-Auth-Group = %v, want [staff]", got)
	}
	if got := zzValuesAs(received, "X-Request-Tag"); !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("X_Request_Tag = %v, want [tag-1] unchanged", got)
	}
}

// A client outside the trusted range loses the reserved headers under their configured names,
// while every other header it sends arrives unchanged.
func TestFuncZZTrustedHeadersUntrustedPeerStripped(t *testing.T) {
	config := dynamic.TrustedHeaders{
		Headers:    []string{"X-Auth-User", "X-Auth-Group"},
		TrustedIPs: []string{"10.0.0.0/8"},
	}
	headers := [][2]string{
		{"X-Auth-User", "alice"},
		{"X-Auth-Group", "staff"},
		{"X-Auth-User-Id", "7"},
		{"X-Request_Tag", "tag-1"},
	}
	status, backend := zzRequest(t, config, headers)
	reached, received := backend.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("untrusted request: status %d, reached backend %v", status, reached)
	}
	if got := zzValuesAs(received, "X-Auth-User"); len(got) != 0 {
		t.Errorf("reserved X-Auth-User = %v, want removed", got)
	}
	if got := zzValuesAs(received, "X-Auth-Group"); len(got) != 0 {
		t.Errorf("reserved X-Auth-Group = %v, want removed", got)
	}
	if got := zzValuesAs(received, "X-Auth-User-Id"); !reflect.DeepEqual(got, []string{"7"}) {
		t.Errorf("X-Auth-User-Id = %v, want [7] unchanged", got)
	}
	if got := zzValuesAs(received, "X-Request-Tag"); !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("X_Request_Tag = %v, want [tag-1] unchanged", got)
	}
}

// Without a trusted range every client is untrusted.
func TestFuncZZTrustedHeadersNoTrustedIPs(t *testing.T) {
	config := dynamic.TrustedHeaders{Headers: []string{"X-Auth-User"}}
	headers := [][2]string{{"X-Auth-User", "alice"}, {"X-Request_Tag", "tag-1"}}
	status, backend := zzRequest(t, config, headers)
	reached, received := backend.seen()
	if status != http.StatusOK || !reached {
		t.Fatalf("request: status %d, reached backend %v", status, reached)
	}
	if got := zzValuesAs(received, "X-Auth-User"); len(got) != 0 {
		t.Errorf("reserved X-Auth-User = %v, want removed", got)
	}
	if got := zzValuesAs(received, "X-Request-Tag"); !reflect.DeepEqual(got, []string{"tag-1"}) {
		t.Errorf("X_Request_Tag = %v, want [tag-1] unchanged", got)
	}
}
