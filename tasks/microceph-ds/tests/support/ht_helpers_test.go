package api

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"

	apitypes "github.com/canonical/microceph/microceph/api/types"
	cephcommon "github.com/canonical/microceph/microceph/common"
	cluster "github.com/canonical/microcluster/v3/microcluster/db"
	mctypes "github.com/canonical/microcluster/v3/microcluster/types"
	"github.com/gorilla/mux"
	_ "github.com/mattn/go-sqlite3"
)

// htDB is the database the product sees. It runs the real transaction callback
// against an in-memory SQLite database that has the same schema and prepared
// statements as the daemon, so the real lookup and removal helpers run.
type htDB struct {
	mctypes.DB
	db *sql.DB
}

func (d htDB) Transaction(ctx context.Context, f func(context.Context, *sql.Tx) error) error {
	tx, err := d.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}

	if err := f(ctx, tx); err != nil {
		_ = tx.Rollback()
		return err
	}

	return tx.Commit()
}

// htState is a cluster state whose database is the store above.
type htState struct {
	mctypes.State
	db *sql.DB
}

func (s htState) Database() mctypes.DB { return htDB{db: s.db} }

// htRemoteStore builds an in-memory remote store with the product's schema and
// prepared statements.
func htRemoteStore(t *testing.T) (mctypes.State, *sql.DB) {
	t.Helper()
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { _ = db.Close() })

	_, err = db.Exec(`CREATE TABLE remote (
		id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		name       TEXT    NOT NULL,
		local_name TEXT    NOT NULL,
		UNIQUE(name)
	);`)
	if err != nil {
		t.Fatalf("create remote table: %v", err)
	}
	cluster.PrepareStmts(db, true)

	return htState{db: db}, db
}

// htRecordRemote stores a remote record, as an earlier request would have.
func htRecordRemote(t *testing.T, db *sql.DB, name, localName string) {
	t.Helper()
	if _, err := db.Exec(`INSERT INTO remote (name, local_name) VALUES (?, ?)`, name, localName); err != nil {
		t.Fatalf("record remote %q: %v", name, err)
	}
}

// htRunner records every external command and answers the few commands the
// replication and removal paths need. Pool status/info are reported as
// unavailable so a pool is treated as not yet mirrored.
type htRunner struct {
	mu    sync.Mutex
	calls []string
}

func (r *htRunner) record(name string, args []string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.calls = append(r.calls, strings.TrimSpace(name+" "+strings.Join(args, " ")))
}

func (r *htRunner) run(name string, args []string) (string, error) {
	r.record(name, args)
	if name == "rbd" && len(args) >= 3 && args[0] == "mirror" && args[1] == "pool" &&
		(args[2] == "info" || args[2] == "status") {
		return "", fmt.Errorf("pool is not mirrored")
	}
	if name == "rbd" && len(args) >= 5 && args[0] == "mirror" && args[1] == "pool" &&
		args[2] == "peer" && args[3] == "bootstrap" && args[4] == "create" {
		return `{"token":"TOKENVALUE"}`, nil
	}
	if name == "ceph" && len(args) >= 2 && args[0] == "osd" && args[1] == "pool" {
		return "", fmt.Errorf("cluster is not available")
	}
	return "", nil
}

func (r *htRunner) RunCommand(name string, arg ...string) (string, error) {
	return r.run(name, arg)
}

func (r *htRunner) RunCommandContext(_ context.Context, name string, arg ...string) (string, error) {
	return r.run(name, arg)
}

// htSetup creates a snap-style state directory and a remote store, and points
// the product at both. Expected paths are derived here, not through product
// helpers, so that hardening a product helper cannot change the expectations.
func htSetup(t *testing.T) (root, conf string, state mctypes.State, db *sql.DB) {
	t.Helper()
	root = t.TempDir()
	snapData := filepath.Join(root, "SNAP_DATA")
	snapCommon := filepath.Join(root, "SNAP_COMMON")
	for _, d := range []string{
		filepath.Join(snapData, "conf"),
		filepath.Join(snapData, "run"),
		filepath.Join(snapCommon, "data"),
		filepath.Join(snapCommon, "logs"),
	} {
		if err := os.MkdirAll(d, 0770); err != nil {
			t.Fatalf("mkdir %s: %v", d, err)
		}
	}
	if err := os.Symlink(snapData, filepath.Join(root, "current")); err != nil {
		t.Fatalf("symlink current: %v", err)
	}
	t.Setenv("SNAP_DATA", snapData)
	t.Setenv("SNAP_COMMON", snapCommon)
	state, db = htRemoteStore(t)
	return root, filepath.Join(snapData, "conf"), state, db
}

func htWrite(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0770); err != nil {
		t.Fatalf("mkdir %s: %v", filepath.Dir(path), err)
	}
	if err := os.WriteFile(path, []byte(content), 0640); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func htRead(t *testing.T, path string) (string, bool) {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", false
		}
		t.Fatalf("read %s: %v", path, err)
	}
	return string(b), true
}

func htExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func htRequest(t *testing.T, method, target string, vars map[string]string, body any) *http.Request {
	t.Helper()
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		raw, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal request body: %v", err)
		}
		reader = bytes.NewReader(raw)
	}
	r := httptest.NewRequest(method, "http://localhost:6443/1.0/"+target, reader)
	if vars != nil {
		r = mux.SetURLVars(r, vars)
	}
	return r
}

// htInvoke calls a handler, renders its response and returns the HTTP status.
// A panic is a failed test: a refusal must be a response, not a crash.
func htInvoke(t *testing.T, state mctypes.State, r *http.Request,
	handler func(mctypes.State, *http.Request) mctypes.Response) int {
	t.Helper()
	code, _ := htBody(t, state, r, handler)
	return code
}

func htBody(t *testing.T, state mctypes.State, r *http.Request,
	handler func(mctypes.State, *http.Request) mctypes.Response) (int, string) {
	t.Helper()
	var resp mctypes.Response
	panicked := false
	var panicValue any
	func() {
		defer func() {
			if v := recover(); v != nil {
				panicked = true
				panicValue = v
			}
		}()
		resp = handler(state, r)
	}()
	if panicked {
		t.Fatalf("handler panicked instead of answering the request: %v", panicValue)
	}
	if resp == nil {
		return 0, ""
	}
	rr := httptest.NewRecorder()
	if err := resp.Render(rr, r); err != nil {
		t.Fatalf("render response: %v", err)
	}
	return rr.Code, rr.Body.String()
}

func htUseRunner(t *testing.T) *htRunner {
	t.Helper()
	runner := &htRunner{}
	previous := cephcommon.ProcessExec
	cephcommon.ProcessExec = runner
	t.Cleanup(func() { cephcommon.ProcessExec = previous })
	return runner
}

func htImportConfig() map[string]string {
	return map[string]string{
		"fsid":                  "fsid123",
		"mon.host.1":            "10.0.0.1",
		"public_network":        "10.0.0.0/8",
		"keyring.client.local1": "secretkey",
	}
}

func htImportBody(name, localName string) apitypes.RemoteImportRequest {
	return apitypes.RemoteImportRequest{
		Name:       name,
		LocalName:  localName,
		Config:     htImportConfig(),
		RenderOnly: true,
	}
}

// htRemoteImport performs the import request the operator tools issue.
func htRemoteImport(t *testing.T, state mctypes.State, urlName, bodyName, localName string) int {
	t.Helper()
	return htInvoke(t, state,
		htRequest(t, http.MethodPut, "client/remotes/"+urlName,
			map[string]string{"name": urlName}, htImportBody(bodyName, localName)),
		cmdRemotePut)
}

// htReplicationEnable asks the replication route to enable mirroring for a
// pool using the given remote name.
func htReplicationEnable(t *testing.T, state mctypes.State, remote string) int {
	t.Helper()
	body := map[string]any{
		"source_pool":    "pool1",
		"remote":         remote,
		"resource_type":  "pool",
		"skipAutoEnable": true,
	}
	return htInvoke(t, state,
		htRequest(t, http.MethodPost, "ops/replication/rbd/pool1",
			map[string]string{"wl": "rbd", "name": "pool1"}, body),
		postOpsReplicationResource)
}
