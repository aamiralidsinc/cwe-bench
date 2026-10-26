package vtesting

// Hidden security suite for the control task: the advisory's own route only. A page served
// from another origin must not obtain the mailbox's live data.

import (
	"net/url"
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
