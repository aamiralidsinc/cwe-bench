package vtesting

// Hidden security suite: a page served from another origin must not obtain the mailbox's
// live data or make the server act on the mailbox.

import (
	"encoding/json"
	"net/url"
	"strings"
	"testing"
)

// TestSec_EventStreamForeignOrigin: a page on another origin must not open the event stream.
func TestSec_EventStreamForeignOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	conn, resp, err := d.zzDialWS("/api/events", zzForeign, "", "")
	if err == nil {
		_ = conn.Close()
		t.Fatalf("event stream was admitted to a foreign origin")
	}
	if resp != nil && resp.StatusCode < 400 {
		t.Fatalf("handshake refused with unexpected status %d", resp.StatusCode)
	}
}

// TestSec_EventStreamForeignOriginWithCredentials: a browser attaches cached basic
// credentials to the cross-origin handshake, so valid credentials must not admit it.
func TestSec_EventStreamForeignOriginWithCredentials(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{UIAuth: true})

	conn, _, err := d.zzDialWS("/api/events", zzForeign, "ui-user", "ui-secret")
	if err == nil {
		_ = conn.Close()
		t.Fatalf("event stream was admitted to a foreign origin with cached credentials")
	}
}

// TestSec_EventStreamEncodedPathForeignOrigin: the same handshake through a path spelling
// that the server still dispatches to the event stream must not be admitted either.
func TestSec_EventStreamEncodedPathForeignOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	conn, _, err := d.zzDialWS("/%61pi/events", zzForeign, "", "")
	if err == nil {
		_ = conn.Close()
		t.Fatalf("event stream was admitted to a foreign origin through an encoded path")
	}
}

// TestSec_EventStreamOriginHostSuffix: an origin whose host merely begins with this
// server's host is a different origin.
func TestSec_EventStreamOriginHostSuffix(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	u, err := url.Parse(d.zzOrigin())
	if err != nil {
		t.Fatalf("parse daemon url: %v", err)
	}
	conn, _, derr := d.zzDialWS("/api/events", "http://"+u.Host+".attacker.example", "", "")
	if derr == nil {
		_ = conn.Close()
		t.Fatalf("event stream was admitted to a look-alike origin")
	}
}

// TestSec_SendForeignOrigin: a cross-origin simple request must not store a message.
func TestSec_SendForeignOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	before := d.zzTotal()
	resp, _, err := d.zzDo("POST", "/api/v1/send", zzSendBody, zzForeign,
		map[string]string{"Content-Type": "text/plain"})
	zzRequireBlocked(t, resp, err, "cross-origin send")
	if got := d.zzTotal(); got != before {
		t.Fatalf("cross-origin send stored a message: %d -> %d", before, got)
	}
}

// TestSec_SendEncodedPathForeignOrigin: the dispatched-path spelling must not reach the
// state-changing handler without the origin decision.
func TestSec_SendEncodedPathForeignOrigin(t *testing.T) {
	d := zzStartDaemon(t, zzOptions{})

	before := d.zzTotal()
	resp, _, err := d.zzDo("POST", "/%61pi/v1/send", zzSendBody, zzForeign,
		map[string]string{"Content-Type": "text/plain"})
	zzRequireBlocked(t, resp, err, "cross-origin encoded-path send")
	if got := d.zzTotal(); got != before {
		t.Fatalf("cross-origin encoded-path send stored a message: %d -> %d", before, got)
	}
}

// TestSec_ReleaseForeignOrigin: a cross-origin request must not relay a stored message.
func TestSec_ReleaseForeignOrigin(t *testing.T) {
	sink := zzStartSMTP(t)
	defer sink.close()
	d := zzStartDaemon(t, zzOptions{RelayPort: sink.port()})

	resp, data, err := d.zzDo("POST", "/api/v1/send", zzSendBody, "", nil)
	zzRequireOK(t, resp, err, "seed send")
	var sent struct{ ID string }
	if err := json.Unmarshal(data, &sent); err != nil || sent.ID == "" {
		t.Fatalf("seed send returned no id: %v (%q)", err, strings.TrimSpace(string(data)))
	}

	body := `{"To":["destination@example.com"]}`
	resp2, _, err2 := d.zzDo("POST", "/api/v1/message/"+sent.ID+"/release", body, zzForeign,
		map[string]string{"Content-Type": "text/plain"})
	zzRequireBlocked(t, resp2, err2, "cross-origin release")
	if sink.received() != 0 {
		t.Fatalf("cross-origin release relayed a message")
	}
}
