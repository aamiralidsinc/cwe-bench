package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
)

// Deleting a saved lock removes the plan file recorded by that lock. The
// recorded project directory and workspace are read back from storage, so they
// must be confined just like request values.

func lockFixture(t *testing.T) (*events.FileWorkspace, models.ProjectLock, string) {
	t.Helper()
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}
	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}
	cloneDir := filepath.Join(dataDir, "repos", "owner", "repo", "1", "default")
	mkdir(t, cloneDir)

	victimDir := filepath.Join(t.TempDir(), "victim")
	mkdir(t, victimDir)
	plan := filepath.Join(victimDir, "default.tfplan")
	writeFile(t, plan, "saved plan")

	lock := models.ProjectLock{
		Project:   models.Project{RepoFullName: "owner/repo", Path: relTo(t, cloneDir, victimDir)},
		Pull:      pull,
		Workspace: "default",
	}
	return wd, lock, plan
}

func TestSec_DeleteLock_StoredProjectPathEscape(t *testing.T) {
	wd, lock, plan := lockFixture(t)
	cmd := &events.DefaultDeleteLockCommand{
		Locker:     &fakeUnlocker{lock: lock},
		WorkingDir: wd,
	}

	if _, err := cmd.DeleteLock(logging.NewNoopLogger(t), "lock-id"); err == nil {
		t.Fatalf("DeleteLock accepted a stored project path outside the workspace")
	}
	mustExist(t, plan)
}

func TestSec_DeleteLocksByPull_StoredProjectPathEscape(t *testing.T) {
	wd, lock, plan := lockFixture(t)
	cmd := &events.DefaultDeleteLockCommand{
		Locker:     &fakeUnlocker{lock: lock, locks: []models.ProjectLock{lock}},
		WorkingDir: wd,
	}

	if _, err := cmd.DeleteLocksByPull(logging.NewNoopLogger(t), "owner/repo", 1); err == nil {
		t.Fatalf("DeleteLocksByPull accepted a stored project path outside the workspace")
	}
	mustExist(t, plan)
}
