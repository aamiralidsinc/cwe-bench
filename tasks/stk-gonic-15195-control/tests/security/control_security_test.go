package vtesting

import (
	"net/url"
	"strings"
	"testing"
)

// The advisory's own route: a private playlist read through the playlist read operation.
// The four cases differ only in the identifier shape and the playlist's location.

func TestSecControlForeignReadRefused(t *testing.T) {
	h := newHarness(t)
	marker := "control-private-marker"
	h.writePlaylist(h.adminDir()+"/private.m3u", marker, "secret", false)

	rec, env := h.do(h.alt, "getPlaylist", url.Values{
		"id": {encodeID(h.adminDir() + "/private.m3u")},
	})
	if !refused(env) || strings.Contains(rec.Body.String(), marker) {
		t.Fatalf("another listener read a private playlist (status=%q)", env.Response.Status)
	}
}

func TestSecControlForeignReadAliasedRefused(t *testing.T) {
	h := newHarness(t)
	marker := "control-aliased-marker"
	h.writePlaylist(h.adminDir()+"/private.m3u", marker, "secret", false)

	alias := h.altDir() + "/../" + h.adminDir() + "/private.m3u"
	rec, env := h.do(h.alt, "getPlaylist", url.Values{"id": {encodeID(alias)}})
	if !refused(env) || strings.Contains(rec.Body.String(), marker) {
		t.Fatalf("an aliased identifier read a private playlist (status=%q)", env.Response.Status)
	}
}

func TestSecControlForeignReadNestedRefused(t *testing.T) {
	h := newHarness(t)
	marker := "control-nested-marker"
	h.writePlaylist(h.adminDir()+"/deep.dir/private.m3u", marker, "secret", false)

	rec, env := h.do(h.alt, "getPlaylist", url.Values{
		"id": {encodeID(h.adminDir() + "/deep.dir/private.m3u")},
	})
	if !refused(env) || strings.Contains(rec.Body.String(), marker) {
		t.Fatalf("a nested private playlist was readable by another listener (status=%q)", env.Response.Status)
	}
}

func TestSecControlForeignReadAliasedNestedRefused(t *testing.T) {
	h := newHarness(t)
	marker := "control-aliased-nested-marker"
	h.writePlaylist(h.adminDir()+"/deep.dir/private.m3u", marker, "secret", false)

	alias := h.altDir() + "/../" + h.adminDir() + "/deep.dir/private.m3u"
	rec, env := h.do(h.alt, "getPlaylist", url.Values{"id": {encodeID(alias)}})
	if !refused(env) || strings.Contains(rec.Body.String(), marker) {
		t.Fatalf("an aliased identifier read a nested private playlist (status=%q)", env.Response.Status)
	}
}
