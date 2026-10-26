package api_test

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/dagu-org/dagu/internal/cmn/config"
	"github.com/dagu-org/dagu/internal/test"
	git "github.com/go-git/go-git/v5"
	gitcfg "github.com/go-git/go-git/v5/config"
	"github.com/go-git/go-git/v5/plumbing/object"
	"github.com/stretchr/testify/require"
)

// taskRaw performs a request without letting the Go HTTP client clean the path, so the
// server sees the exact bytes the client sent.
func taskRaw(t *testing.T, server test.Server, method, requestPath string, body []byte) (int, []byte) {
	t.Helper()
	baseURL := fmt.Sprintf("http://%s:%d", server.Config.Server.Host, server.Config.Server.Port)
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		reader = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, baseURL+requestPath, reader)
	require.NoError(t, err)
	req.URL.RawPath = requestPath
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := http.DefaultClient.Do(req)
	require.NoError(t, err)
	defer func() { _ = resp.Body.Close() }()
	out := new(bytes.Buffer)
	_, _ = out.ReadFrom(resp.Body)
	return resp.StatusCode, out.Bytes()
}

func taskJSON(t *testing.T, value any) []byte {
	t.Helper()
	b, err := json.Marshal(value)
	require.NoError(t, err)
	return b
}

func taskClientError(code int) bool { return code >= 400 && code < 500 }

func taskWrite(t *testing.T, path, content string) {
	t.Helper()
	require.NoError(t, os.MkdirAll(filepath.Dir(path), 0o755))
	require.NoError(t, os.WriteFile(path, []byte(content), 0o600))
}

func taskDAGsDir(t *testing.T) string {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "dags")
	require.NoError(t, os.MkdirAll(dir, 0o755))
	return dir
}

func taskServer(t *testing.T, dagsDir string) test.Server {
	t.Helper()
	return test.SetupServer(t, test.WithDAGsDir(dagsDir))
}

// --- git sync fixture -----------------------------------------------------

func taskGitRemote(t *testing.T, dir string, files map[string]string) {
	t.Helper()
	repo, err := git.PlainInit(dir, false)
	require.NoError(t, err)
	wt, err := repo.Worktree()
	require.NoError(t, err)
	for name, content := range files {
		full := filepath.Join(dir, name)
		taskWrite(t, full, content)
		_, err := wt.Add(name)
		require.NoError(t, err)
	}
	_, err = wt.Commit("fixture", &git.CommitOptions{
		Author: &object.Signature{Name: "task", Email: "task@example.invalid", When: time.Now()},
	})
	require.NoError(t, err)
}

func taskGitClone(t *testing.T, remote, repoPath string) {
	t.Helper()
	require.NoError(t, os.MkdirAll(filepath.Dir(repoPath), 0o755))
	repo, err := git.PlainInit(repoPath, false)
	require.NoError(t, err)
	_, err = repo.CreateRemote(&gitcfg.RemoteConfig{Name: "origin", URLs: []string{remote}})
	require.NoError(t, err)
	require.NoError(t, repo.FetchContext(context.Background(), &git.FetchOptions{
		RemoteName: "origin",
		RefSpecs:   []gitcfg.RefSpec{"+refs/heads/*:refs/remotes/origin/*"},
	}))
	ref, err := repo.Reference("refs/remotes/origin/master", true)
	require.NoError(t, err)
	wt, err := repo.Worktree()
	require.NoError(t, err)
	require.NoError(t, wt.Checkout(&git.CheckoutOptions{
		Branch: "refs/heads/master", Hash: ref.Hash(), Create: true, Force: true,
	}))
}

func taskSyncServer(t *testing.T, remote string) (test.Server, string) {
	t.Helper()
	server := test.SetupServer(t, test.WithConfigMutator(func(cfg *config.Config) {
		cfg.GitSync.Enabled = true
		cfg.GitSync.PushEnabled = true
		cfg.GitSync.Repository = "example.invalid/team/workflows"
		cfg.GitSync.Branch = "master"
		cfg.GitSync.Auth.Type = ""
		cfg.GitSync.AutoSync.Enabled = false
	}))
	dagsDir := server.Config.Paths.DAGsDir
	taskGitClone(t, remote, filepath.Join(server.Config.Paths.DataDir, "gitsync", "repo"))
	return server, dagsDir
}

// --- security tests -------------------------------------------------------

func TestSecReadOutsideDAGsDirectory(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	victim := filepath.Join(filepath.Dir(dagsDir), "secret.yaml")
	const marker = "TASK-MARKER-READ-7f31"
	taskWrite(t, victim, "steps:\n  - command: echo "+marker+"\n")

	server := taskServer(t, dagsDir)
	code, body := taskRaw(t, server, http.MethodGet, "/api/v1/dags/..%2Fsecret/spec", nil)

	require.True(t, taskClientError(code), "expected a client error, got %d", code)
	require.NotContains(t, string(body), marker, "the response exposed a file outside the DAGs directory")
	data, err := os.ReadFile(victim)
	require.NoError(t, err, "the file outside the DAGs directory was removed")
	require.Contains(t, string(data), marker)
}

func TestSecDeleteOutsideDAGsDirectory(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	victim := filepath.Join(filepath.Dir(dagsDir), "secret.yaml")
	taskWrite(t, victim, "steps:\n  - command: echo keep-me\n")

	server := taskServer(t, dagsDir)
	code, _ := taskRaw(t, server, http.MethodDelete, "/api/v1/dags/..%2Fsecret", nil)

	require.True(t, taskClientError(code), "expected a client error, got %d", code)
	_, err := os.Stat(victim)
	require.NoError(t, err, "the file outside the DAGs directory was deleted")
}

func TestSecCreateOutsideDAGsDirectory(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	outside := filepath.Join(t.TempDir(), "planted")
	server := taskServer(t, dagsDir)

	code, _ := taskRaw(t, server, http.MethodPost, "/api/v1/dags",
		taskJSON(t, map[string]any{"name": outside}))

	require.True(t, taskClientError(code), "expected a client error, got %d", code)
	_, err := os.Stat(outside)
	require.True(t, os.IsNotExist(err), "a file was created outside the DAGs directory")
}

func TestSecRenameOutsideDAGsDirectory(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	source := filepath.Join(dagsDir, "source.yaml")
	taskWrite(t, source, "steps:\n  - command: echo source\n")
	// A destination made only of dots resolves to the DAGs directory's parent, and the
	// required extension makes the write land in a file beside that parent.
	target := filepath.Dir(dagsDir) + ".yaml"
	t.Cleanup(func() { _ = os.Remove(target) })

	server := taskServer(t, dagsDir)
	code, _ := taskRaw(t, server, http.MethodPost, "/api/v1/dags/source/rename",
		taskJSON(t, map[string]any{"newFileName": ".."}))

	require.True(t, taskClientError(code), "expected a client error, got %d", code)
	_, err := os.Stat(target)
	require.True(t, os.IsNotExist(err), "a file was created outside the DAGs directory")
	_, err = os.Stat(source)
	require.NoError(t, err, "the DAG inside the DAGs directory was moved")
}

func TestSecSyncEntryOutsideDAGsDirectory(t *testing.T) {
	remote := filepath.Join(t.TempDir(), "remote")
	taskGitRemote(t, remote, map[string]string{
		"%2E%2E%2Fevil.yaml": "steps:\n  - command: echo planted\n",
		"sub/normal.yaml":    "steps:\n  - command: echo normal\n",
	})

	server, dagsDir := taskSyncServer(t, remote)
	outside := filepath.Join(filepath.Dir(dagsDir), "evil.yaml")

	code, body := taskRaw(t, server, http.MethodPost, "/api/v1/sync/pull", []byte("{}"))

	// Either refusal form the instruction allows passes (fairness review 2026-10-23, fixed 2026-10-25):
	// (a) the whole pull is refused with a client error, or (b) the pull succeeds and the escaping
	// entry alone is skipped while the legitimate nested entry syncs. In both, nothing may appear
	// outside the DAGs directory.
	_, err := os.Stat(outside)
	require.True(t, os.IsNotExist(err), "a synced entry was written outside the DAGs directory")
	if code >= 400 && code < 500 {
		return
	}
	require.Equal(t, http.StatusOK, code, "the sync pull neither succeeded nor was refused with a client error: %s", string(body))
	_, err = os.Stat(filepath.Join(dagsDir, "sub", "normal.yaml"))
	require.NoError(t, err, "a legitimate nested entry did not sync")
}
