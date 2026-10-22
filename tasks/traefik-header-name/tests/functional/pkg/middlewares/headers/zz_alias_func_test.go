package headers

import (
	"net/http"
	"reflect"
	"strings"
	"testing"
)

func zzExact(h http.Header, name string) []string {
	var out []string
	for key, values := range h {
		if strings.EqualFold(key, name) {
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
	// zzServe sends the header under test as "X_Request_Tag: zz-spoofed-admin"; nothing manages it.
	if got := zzExact(header, "X_Request_Tag"); !reflect.DeepEqual(got, []string{zzSpoof}) {
		t.Errorf("unrelated X_Request_Tag = %v, want it unchanged (headers %v)", got, header)
	}
	return header
}

func TestFuncZZCustomRequestHeaderSetKeepsOtherHeaders(t *testing.T) {
	status, backend := zzServe(t, map[string]string{"X-Auth-User": "gateway", "X_Static_Tag": "s-1"}, "X_Request_Tag")
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X-Auth-User"); !reflect.DeepEqual(got, []string{"gateway"}) {
		t.Errorf("X-Auth-User = %v, want [gateway]", got)
	}
	if got := zzValuesAs(header, "X_Static_Tag"); !reflect.DeepEqual(got, []string{"s-1"}) {
		t.Errorf("configured X_Static_Tag = %v, want [s-1]", got)
	}
}

func TestFuncZZCustomRequestHeaderRemoveKeepsOtherHeaders(t *testing.T) {
	status, backend := zzServe(t, map[string]string{"X-Auth-User": ""}, "X_Request_Tag")
	header := zzCheckUnrelated(t, status, backend)
	if got := zzValuesAs(header, "X-Auth-User"); len(got) != 0 {
		t.Errorf("X-Auth-User = %v, want removed", got)
	}
}
