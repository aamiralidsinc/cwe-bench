package server

import (
	"reflect"
	"strings"
	"testing"
)

// Request header lines whose name contains an underscore.
var zzUnderscoreLines = map[string]string{
	"underscored":       "X_Auth_User: zz-spoofed-admin",
	"mixed":             "X_Auth-User: zz-spoofed-admin",
	"lower case":        "x_auth_user: zz-spoofed-admin",
	"single underscore": "_: zz-spoofed-admin",
	"unrelated name":    "Custom_Trace: zz-spoofed-admin",
}

// With the entry-point setting at delete, no header whose name contains an underscore reaches
// routing, while the other headers (including several values of one header) arrive unchanged.
func TestSecZZEntryPointUnderscoreHeadersDelete(t *testing.T) {
	eps, err := zzLoadEntryPoints(t, "--entryPoints.web.http.underscoreHeadersStrategy=delete")
	if err != nil {
		t.Fatalf("entry point with underscoreHeadersStrategy=delete: %v", err)
	}
	backend := &zzBackend{}
	addr := zzStart(t, eps, backend)

	for name, line := range zzUnderscoreLines {
		t.Run(name, func(t *testing.T) {
			status := zzRawGet(t, addr, "X-Auth-User: legit-a", "X-Auth-User: legit-b", line)
			reached, header := backend.take()
			if status < 200 || status > 299 || !reached {
				t.Fatalf("legitimate request was not routed: status %d, reached %v", status, reached)
			}
			for key, values := range header {
				if strings.Contains(key, "_") {
					t.Fatalf("header %q=%v reached routing", key, values)
				}
			}
			if got := header["X-Auth-User"]; !reflect.DeepEqual(got, []string{"legit-a", "legit-b"}) {
				t.Fatalf("X-Auth-User = %v, want both values unchanged", got)
			}
		})
	}
}

// With the entry-point setting at reject, a request carrying a header whose name contains an
// underscore is refused with a client error and never routed; other requests are routed.
func TestSecZZEntryPointUnderscoreHeadersReject(t *testing.T) {
	eps, err := zzLoadEntryPoints(t, "--entryPoints.web.http.underscoreHeadersStrategy=reject")
	if err != nil {
		t.Fatalf("entry point with underscoreHeadersStrategy=reject: %v", err)
	}
	backend := &zzBackend{}
	addr := zzStart(t, eps, backend)

	for name, line := range zzUnderscoreLines {
		t.Run(name, func(t *testing.T) {
			status := zzRawGet(t, addr, "X-Auth-User: legit-a", line)
			reached, _ := backend.take()
			if reached || status < 400 || status > 499 {
				t.Fatalf("got status %d, routed %v; want a client error and no routing", status, reached)
			}

			status = zzRawGet(t, addr, "X-Auth-User: legit-a", "X-Trace-Id: 7")
			reached, header := backend.take()
			if status < 200 || status > 299 || !reached || header.Get("X-Auth-User") != "legit-a" {
				t.Fatalf("request without underscores: status %d, routed %v, headers %v", status, reached, header)
			}
		})
	}
}

// The setting accepts keep (headers forwarded as today) and refuses any unknown value at start-up,
// so that a typo cannot silently leave the entry point unprotected.
func TestSecZZEntryPointUnderscoreHeadersValues(t *testing.T) {
	eps, err := zzLoadEntryPoints(t, "--entryPoints.web.http.underscoreHeadersStrategy=keep")
	if err != nil {
		t.Fatalf("entry point with underscoreHeadersStrategy=keep: %v", err)
	}
	backend := &zzBackend{}
	addr := zzStart(t, eps, backend)
	status := zzRawGet(t, addr, "X-Auth-User: legit-a", "Custom_Trace: t-1")
	reached, header := backend.take()
	if status < 200 || status > 299 || !reached {
		t.Fatalf("keep: status %d, routed %v", status, reached)
	}
	if got := header["Custom_trace"]; !reflect.DeepEqual(got, []string{"t-1"}) {
		t.Fatalf("Custom_Trace not forwarded unchanged with keep: %v", header)
	}

	if !zzStartsWith(t, "--entryPoints.web.http.underscoreHeadersStrategy=keep") {
		t.Fatal("start-up probe: entry point with underscoreHeadersStrategy=keep did not serve")
	}
	for _, bad := range []string{"drop", "Delete-All"} {
		if zzStartsWith(t, "--entryPoints.web.http.underscoreHeadersStrategy="+bad) {
			t.Errorf("value %q accepted; want a start-up error", bad)
		}
	}
}
