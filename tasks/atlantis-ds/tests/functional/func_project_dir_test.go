package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
)

// The default project directory is the checkout root itself, and nested project
// directories are ordinary. Both must keep running steps where they always did.

func TestFunc_ProjectDir_DefaultDirectory(t *testing.T) {
	repoDir := t.TempDir()
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", ".", "", initStep())

	if err := runner.Plan(ctx).Error; err != nil {
		t.Fatalf("Plan refused the repository root as a project directory: %v", err)
	}
	mustExist(t, filepath.Join(repoDir, step.name))
}

func TestFunc_ProjectDir_NestedDirectory(t *testing.T) {
	repoDir := t.TempDir()
	nested := filepath.Join(repoDir, "modules", "vpc")
	mkdir(t, nested)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", "modules/vpc", "", initStep())

	if err := runner.Plan(ctx).Error; err != nil {
		t.Fatalf("Plan refused a nested project directory: %v", err)
	}
	mustExist(t, filepath.Join(nested, step.name))
}

func TestFunc_ProjectDir_ApplyNestedDirectory(t *testing.T) {
	repoDir := t.TempDir()
	nested := filepath.Join(repoDir, "modules", "vpc")
	mkdir(t, nested)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", "modules/vpc", "", initStep())

	if err := runner.Apply(ctx).Error; err != nil {
		t.Fatalf("Apply refused a nested project directory: %v", err)
	}
	mustExist(t, filepath.Join(nested, step.name))
}

func TestFunc_DeletePlan_LegitimateFile(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}
	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	plan := filepath.Join(dataDir, "repos", "owner", "repo", "1", "default", "modules", "vpc", "default.tfplan")
	writeFile(t, plan, "plan bytes")

	if err := wd.DeletePlan(logging.NewNoopLogger(t), repo, pull, "default", "modules/vpc", ""); err != nil {
		t.Fatalf("DeletePlan refused a legitimate plan file: %v", err)
	}
	mustNotExist(t, plan)
}

func TestFunc_DeleteLock_LegitimateFile(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}
	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	plan := filepath.Join(dataDir, "repos", "owner", "repo", "1", "default", "modules", "vpc", "default.tfplan")
	writeFile(t, plan, "plan bytes")

	lock := models.ProjectLock{
		Project:   models.Project{RepoFullName: "owner/repo", Path: "modules/vpc"},
		Pull:      pull,
		Workspace: "default",
	}
	cmd := &events.DefaultDeleteLockCommand{
		Locker:     &fakeUnlocker{lock: lock},
		WorkingDir: wd,
	}
	if _, err := cmd.DeleteLock(logging.NewNoopLogger(t), "lock-id"); err != nil {
		t.Fatalf("DeleteLock refused a legitimate saved lock: %v", err)
	}
	mustNotExist(t, plan)
}
