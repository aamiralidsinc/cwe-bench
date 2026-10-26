package vtesting

// Hidden functional suite: legitimate clients keep working, including the values that sit
// next to the origin decision (same-origin browsers, clients that send no origin, a
// configured cross-origin policy, a non-root webroot and the credential-less preflight).

import (
	"encoding/json"
	"testing"
)

// TestFunc_EventStreamSameOrigin: the bundled web UI connects from this server's origin.
func TestFunc_EventStreamSameOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	conn, _, err := d.zzDialWS("/api/events", d.zzOrigin(), "", "")
	if err != nil {
		t.Fatalf("same-origin event stream was refused: %v", err)
	}
	_ = conn.Close()
}

// TestFunc_EventStreamNoOrigin: command-line and service clients send no Origin header.
func TestFunc_EventStreamNoOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	conn, _, err := d.zzDialWS("/api/events", "", "", "")
	if err != nil {
		t.Fatalf("origin-less event stream was refused: %v", err)
	}
	_ = conn.Close()
}

// TestFunc_EventStreamWebroot: the socket lives under the configured webroot.
func TestFunc_EventStreamWebroot(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{Webroot: "/mail/"})

	conn, _, err := d.zzDialWS("/mail/api/events", d.zzOrigin(), "", "")
	if err != nil {
		t.Fatalf("webroot event stream was refused: %v", err)
	}
	_ = conn.Close()
}

// TestFunc_SendNoOrigin: local scripts and CI post without an Origin header or a JSON
// content type.
func TestFunc_SendNoOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	before := d.zzTotal()
	resp, _, err := d.zzDo("POST", "/api/v1/send", zzSendBody, "",
		map[string]string{"Content-Type": "text/plain"})
	zzRequireOK(t, resp, err, "origin-less send")
	if got := d.zzTotal(); got != before+1 {
		t.Fatalf("origin-less send did not store the message: %d -> %d", before, got)
	}
}

// TestFunc_SendSameOrigin: the web UI's own send action.
func TestFunc_SendSameOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	resp, _, err := d.zzDo("POST", "/api/v1/send", zzSendBody, d.zzOrigin(), nil)
	zzRequireOK(t, resp, err, "same-origin send")
}

// TestFunc_SendConfiguredOrigin: an operator-configured trusted origin may post, and
// still receives the CORS grant on API paths.
func TestFunc_SendConfiguredOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{APICORS: "http://trusted.example"})

	resp, _, err := d.zzDo("POST", "/api/v1/send", zzSendBody, "http://trusted.example", nil)
	zzRequireOK(t, resp, err, "configured-origin send")

	info, _, err := d.zzDo("GET", "/api/v1/info", "", "http://trusted.example", nil)
	zzRequireOK(t, info, err, "configured-origin API read")
	if got := info.Header.Get("Access-Control-Allow-Origin"); got != "http://trusted.example" {
		t.Fatalf("CORS grant on an API path was %q", got)
	}
}

// TestFunc_CorsPreflight: browsers send the preflight without credentials; it must keep
// being answered when cross-origin use is configured.
func TestFunc_CorsPreflight(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{APICORS: "http://trusted.example", UIAuth: true})

	resp, _, err := d.zzDo("OPTIONS", "/api/v1/send", "", "http://trusted.example",
		map[string]string{"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
	zzRequireOK(t, resp, err, "CORS preflight")
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "http://trusted.example" {
		t.Fatalf("preflight lost the CORS grant: %q", got)
	}
}

// TestFunc_WildcardOrigin: the documented wildcard keeps allowing any configured origin.
func TestFunc_WildcardOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{APICORS: "*"})

	resp, _, err := d.zzDo("POST", "/api/v1/send", zzSendBody, "http://another.example", nil)
	zzRequireOK(t, resp, err, "wildcard-origin send")
}

// TestFunc_ReleaseNoOrigin: a scripted relay keeps working without an Origin header.
func TestFunc_ReleaseNoOrigin(t *testing.T) {
	sink := zzStartSMTP(t)
	defer sink.close()
	d := zzStartDaemon(t, zzOptions{RelayPort: sink.port()})

	// Seed a message through the public send endpoint, then relay it.
	resp, data, err := d.zzDo("POST", "/api/v1/send", zzSendBody, "", nil)
	zzRequireOK(t, resp, err, "seed send")
	var sent struct{ ID string }
	if err := json.Unmarshal(data, &sent); err != nil || sent.ID == "" {
		t.Fatalf("seed send returned no id: %v", err)
	}

	body := `{"To":["destination@example.com"]}`
	resp2, _, err2 := d.zzDo("POST", "/api/v1/message/"+sent.ID+"/release", body, "", nil)
	zzRequireOK(t, resp2, err2, "origin-less release")
	if sink.received() != 1 {
		t.Fatalf("origin-less release did not reach the relay")
	}
}
