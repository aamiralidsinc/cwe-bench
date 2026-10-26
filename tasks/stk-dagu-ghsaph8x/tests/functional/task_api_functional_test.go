package api_test

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"
)

const taskSpecAlpha = "steps:\n  - command: echo alpha\n"
const taskSpecBeta = "steps:\n  - command: echo beta\n"

func taskDecode(t *testing.T, body []byte, out any) {
	t.Helper()
	require.NoError(t, json.Unmarshal(body, out), "unexpected response body: %s", string(body))
}

func TestFuncCreateReadUpdateDelete(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	server := taskServer(t, dagsDir)
	path := "/api/v1/dags/alpha.dag-1"

	code, body := taskRaw(t, server, http.MethodPost, "/api/v1/dags",
		taskJSON(t, map[string]any{"name": "alpha.dag-1", "spec": taskSpecAlpha}))
	require.Equal(t, http.StatusCreated, code, "creating a DAG failed: %s", string(body))
	require.FileExists(t, filepath.Join(dagsDir, "alpha.dag-1.yaml"))

	code, body = taskRaw(t, server, http.MethodGet, path+"/spec", nil)
	require.Equal(t, http.StatusOK, code, "reading the DAG spec failed: %s", string(body))
	var spec struct {
		Spec string `json:"spec"`
	}
	taskDecode(t, body, &spec)
	require.Contains(t, spec.Spec, "echo alpha")

	code, body = taskRaw(t, server, http.MethodPut, path+"/spec",
		taskJSON(t, map[string]any{"spec": taskSpecBeta}))
	require.Equal(t, http.StatusOK, code, "updating the DAG spec failed: %s", string(body))

	code, body = taskRaw(t, server, http.MethodGet, path+"/spec", nil)
	require.Equal(t, http.StatusOK, code)
	spec.Spec = ""
	taskDecode(t, body, &spec)
	require.Contains(t, spec.Spec, "echo beta")

	code, body = taskRaw(t, server, http.MethodDelete, path, nil)
	require.Equal(t, http.StatusNoContent, code, "deleting the DAG failed: %s", string(body))
	_, err := os.Stat(filepath.Join(dagsDir, "alpha.dag-1.yaml"))
	require.True(t, os.IsNotExist(err), "the DAG file still exists after deletion")
}

func TestFuncCreateWithDefaultSpec(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	server := taskServer(t, dagsDir)

	code, body := taskRaw(t, server, http.MethodPost, "/api/v1/dags",
		taskJSON(t, map[string]any{"name": "default-one"}))
	require.Equal(t, http.StatusCreated, code, "creating a DAG without a spec failed: %s", string(body))
	require.FileExists(t, filepath.Join(dagsDir, "default-one.yaml"))

	code, body = taskRaw(t, server, http.MethodGet, "/api/v1/dags/default-one/spec", nil)
	require.Equal(t, http.StatusOK, code, "reading the default DAG spec failed: %s", string(body))
	var spec struct {
		Spec string `json:"spec"`
	}
	taskDecode(t, body, &spec)
	require.Contains(t, spec.Spec, "echo hello")
}

func TestFuncRenameToDottedName(t *testing.T) {
	dagsDir := taskDAGsDir(t)
	taskWrite(t, filepath.Join(dagsDir, "old-name.yaml"), taskSpecAlpha)
	server := taskServer(t, dagsDir)

	code, body := taskRaw(t, server, http.MethodPost, "/api/v1/dags/old-name/rename",
		taskJSON(t, map[string]any{"newFileName": "new.name_2"}))
	require.Equal(t, http.StatusOK, code, "renaming to a dotted name failed: %s", string(body))
	require.FileExists(t, filepath.Join(dagsDir, "new.name_2.yaml"))
	_, err := os.Stat(filepath.Join(dagsDir, "old-name.yaml"))
	require.True(t, os.IsNotExist(err), "the old DAG file still exists after renaming")
}

func TestFuncSyncNestedEntries(t *testing.T) {
	remote := filepath.Join(t.TempDir(), "remote")
	taskGitRemote(t, remote, map[string]string{
		"sub/normal.yaml":  taskSpecAlpha,
		"memory/MEMORY.md": "# memory\n",
	})
	server, dagsDir := taskSyncServer(t, remote)

	code, body := taskRaw(t, server, http.MethodPost, "/api/v1/sync/pull", []byte("{}"))
	require.Equal(t, http.StatusOK, code, "the sync pull failed: %s", string(body))
	var result struct {
		Success bool `json:"success"`
	}
	taskDecode(t, body, &result)
	require.True(t, result.Success, "the sync pull reported failure: %s", string(body))

	require.FileExists(t, filepath.Join(dagsDir, "sub", "normal.yaml"))
	require.FileExists(t, filepath.Join(dagsDir, "memory", "MEMORY.md"))
}
