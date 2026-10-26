package api

import (
	"net/http"
	"path/filepath"
	"strings"
	"testing"

	apitypes "github.com/canonical/microceph/microceph/api/types"
)

// TestSecImportNameCannotEscapeConfigArea drives the documented import flow
// with a name that walks out of the configuration area. The request must be
// refused and nothing may be produced outside the area.
func TestSecImportNameCannotEscapeConfigArea(t *testing.T) {
	root, _, state, _ := htSetup(t)

	code := htRemoteImport(t, state, "../../escape", "../../escape", "local1")
	if code < 400 {
		t.Fatalf("import with a traversal name was not refused: status %d", code)
	}
	for _, name := range []string{"escape.conf", "escape.keyring"} {
		if htExists(filepath.Join(root, name)) {
			t.Fatalf("import created %s outside the configuration area", name)
		}
	}
}

// TestSecImportCannotReplaceLocalConfigFiles drives the import flow with
// names that pass the character rules but name files the local cluster owns.
func TestSecImportCannotReplaceLocalConfigFiles(t *testing.T) {
	for _, reserved := range []string{"ceph", "radosgw"} {
		t.Run(reserved, func(t *testing.T) {
			_, conf, state, _ := htSetup(t)
			existing := map[string]string{
				"ceph.conf":    "LOCAL-CEPH-CONF",
				"ceph.keyring": "LOCAL-CEPH-KEYRING",
				"radosgw.conf": "LOCAL-RADOSGW-CONF",
			}
			for name, content := range existing {
				htWrite(t, filepath.Join(conf, name), content)
			}

			code := htRemoteImport(t, state, reserved, reserved, "local1")
			if code < 400 {
				t.Fatalf("import of reserved name %q was not refused: status %d", reserved, code)
			}
			for name, content := range existing {
				got, ok := htRead(t, filepath.Join(conf, name))
				if !ok {
					t.Fatalf("import of %q removed the local file %s", reserved, name)
				}
				if got != content {
					t.Fatalf("import of %q replaced the local file %s", reserved, name)
				}
			}
		})
	}
}

// TestSecImportStaysOnAddressedRemote checks that a request naming one remote
// in its path cannot create the files of a different remote named in the body.
func TestSecImportStaysOnAddressedRemote(t *testing.T) {
	t.Run("two different names", func(t *testing.T) {
		_, conf, state, _ := htSetup(t)
		code := htRemoteImport(t, state, "alpha", "beta", "local1")
		if code < 400 {
			t.Fatalf("mismatched path and body names were accepted: status %d", code)
		}
		for _, name := range []string{"alpha.conf", "alpha.keyring", "beta.conf", "beta.keyring"} {
			if htExists(filepath.Join(conf, name)) {
				t.Fatalf("mismatched request produced %s", name)
			}
		}
	})

	t.Run("traversal in path with clean body", func(t *testing.T) {
		root, conf, state, _ := htSetup(t)
		code := htRemoteImport(t, state, "../../escape", "beta", "local1")
		if code < 400 {
			t.Fatalf("a traversal name in the path was accepted: status %d", code)
		}
		for _, name := range []string{"beta.conf", "beta.keyring"} {
			if htExists(filepath.Join(conf, name)) {
				t.Fatalf("request produced %s", name)
			}
		}
		if htExists(filepath.Join(root, "escape.conf")) || htExists(filepath.Join(root, "escape.keyring")) {
			t.Fatalf("request produced files outside the configuration area")
		}
	})
}

// TestSecImportRejectsInjectedLocalName drives the import flow with a local
// name that tries to add its own line to the generated keyring.
func TestSecImportRejectsInjectedLocalName(t *testing.T) {
	const marker = "RBD_CACHE_INJECTED_MARKER"
	_, conf, state, _ := htSetup(t)

	code := htRemoteImport(t, state, "good", "good", "local1\n\trbd_cache = "+marker)
	if code < 400 {
		t.Fatalf("import with an injected local name was accepted: status %d", code)
	}
	keyring, ok := htRead(t, filepath.Join(conf, "good.keyring"))
	if ok && strings.Contains(keyring, marker) {
		t.Fatalf("generated keyring contains attacker supplied content")
	}
}

// TestSecImportRejectsOverlongName checks the accepted length bound.
func TestSecImportRejectsOverlongName(t *testing.T) {
	_, conf, state, _ := htSetup(t)
	name := strings.Repeat("a", 64)

	code := htRemoteImport(t, state, name, name, "local1")
	if code < 400 {
		t.Fatalf("import with an over-long name was accepted: status %d", code)
	}
	if htExists(filepath.Join(conf, name+".conf")) || htExists(filepath.Join(conf, name+".keyring")) {
		t.Fatalf("over-long name produced files")
	}
}

// TestSecRemoveNameCannotEscapeConfigArea drives the removal flow with a name
// that walks out of the configuration area.
func TestSecRemoveNameCannotEscapeConfigArea(t *testing.T) {
	root, _, state, db := htSetup(t)
	htRecordRemote(t, db, "../../victim", "local1")
	targets := []string{filepath.Join(root, "victim.conf"), filepath.Join(root, "victim.keyring")}
	for _, p := range targets {
		htWrite(t, p, "DO-NOT-REMOVE")
	}
	htUseRunner(t)

	code := htInvoke(t, state,
		htRequest(t, http.MethodDelete, "client/remotes/../../victim",
			map[string]string{"name": "../../victim"}, nil),
		cmdRemoteDelete)
	if code < 400 {
		t.Fatalf("removal with a traversal name was not refused: status %d", code)
	}
	for _, p := range targets {
		if !htExists(p) {
			t.Fatalf("removal deleted %s outside the configuration area", p)
		}
	}
}

// TestSecRemoveCannotDeleteLocalConfigFiles drives the removal flow with the
// names of files the local cluster owns.
func TestSecRemoveCannotDeleteLocalConfigFiles(t *testing.T) {
	for _, reserved := range []string{"ceph", "radosgw"} {
		t.Run(reserved, func(t *testing.T) {
			_, conf, state, db := htSetup(t)
			htRecordRemote(t, db, reserved, "local1")
			targets := []string{
				filepath.Join(conf, reserved+".conf"),
				filepath.Join(conf, reserved+".keyring"),
			}
			for _, p := range targets {
				htWrite(t, p, "DO-NOT-REMOVE")
			}
			htUseRunner(t)

			code := htInvoke(t, state,
				htRequest(t, http.MethodDelete, "client/remotes/"+reserved,
					map[string]string{"name": reserved}, nil),
				cmdRemoteDelete)
			if code < 400 {
				t.Fatalf("removal of reserved name %q was not refused: status %d", reserved, code)
			}
			for _, p := range targets {
				if !htExists(p) {
					t.Fatalf("removal deleted the local file %s", p)
				}
			}
		})
	}
}

// TestSecRefreshNameCannotEscapeConfigArea drives the remote refresh flow with
// a name that walks out of the configuration area.
func TestSecRefreshNameCannotEscapeConfigArea(t *testing.T) {
	root, _, state, _ := htSetup(t)
	body := apitypes.RemoteImportRequest{LocalName: "local1", Config: htImportConfig()}

	code := htInvoke(t, state,
		htRequest(t, http.MethodPut, "client/remotes/../../victim/refresh",
			map[string]string{"name": "../../victim"}, body),
		cmdRemoteRefresh)
	if code < 400 {
		t.Fatalf("refresh with a traversal name was not refused: status %d", code)
	}
	for _, name := range []string{"victim.conf", "victim.keyring"} {
		if htExists(filepath.Join(root, name)) {
			t.Fatalf("refresh produced %s outside the configuration area", name)
		}
	}
}

// TestSecBulkRemoveNameCannotEscapeConfigArea drives the bulk removal flow
// with a name that walks out of the configuration area.
func TestSecBulkRemoveNameCannotEscapeConfigArea(t *testing.T) {
	root, _, state, db := htSetup(t)
	htRecordRemote(t, db, "../../victim", "local1")
	targets := []string{filepath.Join(root, "victim.conf"), filepath.Join(root, "victim.keyring")}
	for _, p := range targets {
		htWrite(t, p, "DO-NOT-REMOVE")
	}
	htUseRunner(t)

	body := apitypes.RemoteBulkDeleteRequest{Names: []string{"../../victim"}}
	code := htInvoke(t, state,
		htRequest(t, http.MethodDelete, "client/remotes", nil, body),
		cmdRemoteBulkDelete)
	if code < 400 {
		t.Fatalf("bulk removal with a traversal name was not refused: status %d", code)
	}
	for _, p := range targets {
		if !htExists(p) {
			t.Fatalf("bulk removal deleted %s outside the configuration area", p)
		}
	}
}

// TestSecStoredRemoteNameCannotEscapeMirrorArea drives the replication flow
// with a remote that was recorded by an earlier request. The name reaches the
// peer token file through stored state rather than through this request.
func TestSecStoredRemoteNameCannotEscapeMirrorArea(t *testing.T) {
	root, _, state, db := htSetup(t)
	htRecordRemote(t, db, "../../victim", "local1")
	sentinel := filepath.Join(root, "SNAP_DATA", "victim_peer_keyring")
	htWrite(t, sentinel, "SENTINEL")
	htUseRunner(t)

	code := htReplicationEnable(t, state, "../../victim")
	if code < 400 {
		t.Fatalf("replication with a stored traversal name was not refused: status %d", code)
	}
	got, ok := htRead(t, sentinel)
	if !ok {
		t.Fatalf("replication removed %s outside the configuration area", sentinel)
	}
	if got != "SENTINEL" {
		t.Fatalf("replication replaced a file outside the configuration area")
	}
}
