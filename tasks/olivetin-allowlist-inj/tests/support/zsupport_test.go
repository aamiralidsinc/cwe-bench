package executor

// Shared helpers for the hidden security and functional suites. Copied into the
// executor package at grading time and compiled alongside both groups.

import (
	"os"
	"path/filepath"
	"testing"

	authpublic "github.com/OliveTin/OliveTin/internal/auth/authpublic"
	config "github.com/OliveTin/OliveTin/internal/config"
)

// runOTAction runs one action through the real executor chain (the same
// ExecRequest path the API, webhook and trigger callers use) and waits for it
// to finish. It mirrors the project's own executor tests.
func runOTAction(t *testing.T, act *config.Action, user *authpublic.AuthenticatedUser, args map[string]string) *ExecutionRequest {
	t.Helper()

	cfg := config.DefaultConfig()
	cfg.Actions = append(cfg.Actions, act)
	cfg.Sanitize()

	e := DefaultExecutor(cfg)
	e.RebuildActionMap()

	if args == nil {
		args = map[string]string{}
	}

	req := &ExecutionRequest{
		AuthenticatedUser: user,
		Cfg:               cfg,
		Arguments:         args,
		Binding:           e.FindBindingWithNoEntity(act),
	}

	wg, _ := e.ExecRequest(req)
	wg.Wait()

	return req
}

// otTempFile returns a path to a not-yet-created file inside the test's own
// temp directory (cleaned up by the test framework).
func otTempFile(t *testing.T, name string) string {
	t.Helper()
	return filepath.Join(t.TempDir(), name)
}

func otFileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func otReadFile(t *testing.T, path string) string {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return string(b)
}

func otUser(username string) *authpublic.AuthenticatedUser {
	return &authpublic.AuthenticatedUser{Username: username}
}
