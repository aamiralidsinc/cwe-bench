package server

import (
	"reflect"
	"testing"

	"github.com/traefik/traefik/v2/pkg/config/static"
)

func zzCheckForwardedAsIs(t *testing.T, addr string, backend *zzBackend) {
	t.Helper()
	status := zzRawGet(t, addr, "X-Auth-User: legit-a", "X-Auth-User: legit-b", "Custom_Trace: t-1", "X_Auth_Role: viewer")
	reached, header := backend.take()
	if status != 200 || !reached {
		t.Fatalf("status %d, routed %v", status, reached)
	}
	want := map[string][]string{
		"X-Auth-User":  {"legit-a", "legit-b"},
		"Custom_trace": {"t-1"},
		"X_auth_role":  {"viewer"},
	}
	for k, v := range want {
		if got := header[k]; !reflect.DeepEqual(got, v) {
			t.Errorf("%s = %v, want %v (headers %v)", k, got, v, header)
		}
	}
}

// By default the entry point forwards headers with underscores in their names as today.
func TestFuncZZEntryPointDefaultForwardsUnderscoreHeaders(t *testing.T) {
	eps, err := zzLoadEntryPoints(t)
	if err != nil {
		t.Fatal(err)
	}
	backend := &zzBackend{}
	zzCheckForwardedAsIs(t, zzStart(t, eps, backend), backend)
}

// Same for an entry point built from a configuration without defaults applied.
func TestFuncZZEntryPointZeroConfigForwardsUnderscoreHeaders(t *testing.T) {
	transport := &static.EntryPointsTransport{}
	transport.SetDefaults()
	ep, err := NewTCPEntryPoint(t.Context(), &static.EntryPoint{
		Address:          "127.0.0.1:0",
		Transport:        transport,
		ForwardedHeaders: &static.ForwardedHeaders{},
		HTTP2:            &static.HTTP2Config{},
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	backend := &zzBackend{}
	zzCheckForwardedAsIs(t, zzStart(t, TCPEntryPoints{"web": ep}, backend), backend)
}
