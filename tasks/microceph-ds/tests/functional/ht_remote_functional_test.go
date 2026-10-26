package api

import (
	"net/http"
	"path/filepath"
	"strings"
	"testing"

	apitypes "github.com/canonical/microceph/microceph/api/types"
	cephlib "github.com/canonical/microceph/microceph/ceph"
)

// TestFuncImportValidRemotes keeps the ordinary import flow working for names
// that satisfy the rules, including names that only resemble a reserved name.
func TestFuncImportValidRemotes(t *testing.T) {
	names := []string{"a", "remote1", "abc123", "ceph1", "radosgw2", strings.Repeat("b", 63)}
	for _, name := range names {
		t.Run(name, func(t *testing.T) {
			_, conf, state, _ := htSetup(t)
			code := htRemoteImport(t, state, name, name, "local1")
			if code != 200 {
				t.Fatalf("valid import of %q returned %d", name, code)
			}
			confData, ok := htRead(t, filepath.Join(conf, name+".conf"))
			if !ok {
				t.Fatalf("valid import of %q did not write its configuration", name)
			}
			if !strings.Contains(confData, "fsid = fsid123") {
				t.Fatalf("configuration for %q lacks the supplied fsid", name)
			}
			keyring, ok := htRead(t, filepath.Join(conf, name+".keyring"))
			if !ok {
				t.Fatalf("valid import of %q did not write its keyring", name)
			}
			if !strings.Contains(keyring, "[client.local1]") {
				t.Fatalf("keyring for %q lacks the local name section", name)
			}
		})
	}
}

// TestFuncListRemotes keeps the collection lookup working for every remote.
func TestFuncListRemotes(t *testing.T) {
	_, _, state, db := htSetup(t)
	htRecordRemote(t, db, "remote1", "local1")
	htRecordRemote(t, db, "remote2", "local2")

	code, body := htBody(t, state,
		htRequest(t, http.MethodGet, "client/remotes", nil, nil),
		cmdRemoteGet)
	if code != 200 {
		t.Fatalf("listing remotes returned %d", code)
	}
	for _, want := range []string{"remote1", "remote2"} {
		if !strings.Contains(body, want) {
			t.Fatalf("listing remotes did not include %q", want)
		}
	}
}

// TestFuncGetRemote keeps the single remote lookup working.
func TestFuncGetRemote(t *testing.T) {
	_, _, state, db := htSetup(t)
	htRecordRemote(t, db, "remote1", "local1")

	code, body := htBody(t, state,
		htRequest(t, http.MethodGet, "client/remotes/remote1", map[string]string{"name": "remote1"}, nil),
		cmdRemoteGet)
	if code != 200 {
		t.Fatalf("fetching a remote returned %d", code)
	}
	if !strings.Contains(body, "remote1") {
		t.Fatalf("fetched remote is missing from the response")
	}
}

// TestFuncRemoveRemote keeps the ordinary removal flow working.
func TestFuncRemoveRemote(t *testing.T) {
	_, conf, state, db := htSetup(t)
	htRecordRemote(t, db, "remote1", "local1")
	targets := []string{filepath.Join(conf, "remote1.conf"), filepath.Join(conf, "remote1.keyring")}
	for _, p := range targets {
		htWrite(t, p, "REMOTE")
	}
	htUseRunner(t)

	code := htInvoke(t, state,
		htRequest(t, http.MethodDelete, "client/remotes/remote1", map[string]string{"name": "remote1"}, nil),
		cmdRemoteDelete)
	if code != 200 {
		t.Fatalf("removing a valid remote returned %d", code)
	}
	for _, p := range targets {
		if htExists(p) {
			t.Fatalf("removing a valid remote left %s behind", p)
		}
	}
}

// TestFuncRefreshRemote keeps the refresh flow working for a valid remote.
func TestFuncRefreshRemote(t *testing.T) {
	_, conf, state, _ := htSetup(t)
	body := apitypes.RemoteImportRequest{LocalName: "local1", Config: htImportConfig()}

	code := htInvoke(t, state,
		htRequest(t, http.MethodPut, "client/remotes/remote1/refresh",
			map[string]string{"name": "remote1"}, body),
		cmdRemoteRefresh)
	if code != 200 {
		t.Fatalf("refreshing a valid remote returned %d", code)
	}
	keyring, ok := htRead(t, filepath.Join(conf, "remote1.keyring"))
	if !ok {
		t.Fatalf("refresh did not write the keyring")
	}
	if !strings.Contains(keyring, "[client.local1]") {
		t.Fatalf("refreshed keyring lacks the local name section")
	}
	if _, ok := htRead(t, filepath.Join(conf, "remote1.conf")); !ok {
		t.Fatalf("refresh did not write the configuration")
	}
}

// TestFuncBulkRemoveRemotes keeps the bulk removal flow working.
func TestFuncBulkRemoveRemotes(t *testing.T) {
	_, conf, state, db := htSetup(t)
	var targets []string
	for _, name := range []string{"remote1", "remote2"} {
		htRecordRemote(t, db, name, "local1")
		for _, ext := range []string{".conf", ".keyring"} {
			p := filepath.Join(conf, name+ext)
			targets = append(targets, p)
			htWrite(t, p, "REMOTE")
		}
	}
	htUseRunner(t)

	body := apitypes.RemoteBulkDeleteRequest{Names: []string{"remote1", "remote2"}}
	code := htInvoke(t, state,
		htRequest(t, http.MethodDelete, "client/remotes", nil, body),
		cmdRemoteBulkDelete)
	if code != 200 {
		t.Fatalf("bulk removal of valid remotes returned %d", code)
	}
	for _, p := range targets {
		if htExists(p) {
			t.Fatalf("bulk removal left %s behind", p)
		}
	}
}

// TestFuncConfigWriterKeepsLocalFileNames keeps the shared writer working for
// the plain file names the rest of the product passes to it.
func TestFuncConfigWriterKeepsLocalFileNames(t *testing.T) {
	_, conf, _, _ := htSetup(t)

	data := map[string]any{
		"fsid":     "fsid123",
		"runDir":   "/run/snap",
		"monitors": "10.0.0.1",
		"pubNet":   "10.0.0.0/8",
		"ipv4":     true,
		"ipv6":     false,
	}
	for _, name := range []string{"ceph.conf", "radosgw.conf", "ganesha.conf", "tmp_ceph.conf"} {
		cfg := cephlib.NewCephConfig(name)
		if err := cfg.WriteConfig(data, 0644); err != nil {
			t.Fatalf("writer rejected the plain file name %q: %v", name, err)
		}
		if !htExists(filepath.Join(conf, name)) {
			t.Fatalf("writer did not produce %q", name)
		}
	}

	keyring := cephlib.NewCephKeyring(conf, "ceph.client.admin.keyring")
	if err := keyring.WriteConfig(map[string]any{"name": "client.admin", "key": "secretkey"}, 0640); err != nil {
		t.Fatalf("writer rejected a plain keyring file name: %v", err)
	}
	if !htExists(filepath.Join(conf, "ceph.client.admin.keyring")) {
		t.Fatalf("writer did not produce the keyring")
	}
}

// TestFuncStoredRemoteTokenWritten keeps the replication flow working for a
// remote that was recorded by an earlier request.
func TestFuncStoredRemoteTokenWritten(t *testing.T) {
	_, conf, state, db := htSetup(t)
	htRecordRemote(t, db, "remote1", "local1")
	htUseRunner(t)

	code := htReplicationEnable(t, state, "remote1")
	if code != 200 {
		t.Fatalf("replication for a valid stored remote returned %d", code)
	}
	token, ok := htRead(t, filepath.Join(conf, "rbd_mirror", "remote1_peer_keyring"))
	if !ok {
		t.Fatalf("replication did not write the peer token")
	}
	if !strings.Contains(token, "TOKENVALUE") {
		t.Fatalf("peer token file does not hold the generated token")
	}
}
