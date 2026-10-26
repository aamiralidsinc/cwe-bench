package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
)

// Ordinary repository identities and workspaces must keep working exactly as
// before: owners that contain "/" (GitLab subgroups, Azure DevOps owners),
// plain repository names, and ordinary workspace names.

func TestFunc_WorkingDir_SubgroupRepoIdentity(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	repo := models.Repo{FullName: "group/subgroup/repo"}
	pull := models.PullRequest{Num: 7, BaseRepo: repo}
	pullDir := filepath.Join(dataDir, "repos", "group", "subgroup", "repo", "7")
	mkdir(t, pullDir)
	writeFile(t, filepath.Join(pullDir, "workspace-file"), "content")

	if err := wd.Delete(logging.NewNoopLogger(t), repo, pull); err != nil {
		t.Fatalf("Delete refused a legitimate repository identity: %v", err)
	}
	mustNotExist(t, pullDir)
}

func TestFunc_WorkingDir_OrdinaryWorkspace(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 3, BaseRepo: repo}
	workspaceDir := filepath.Join(dataDir, "repos", "owner", "repo", "3", "my-workspace")
	mkdir(t, workspaceDir)
	writeFile(t, filepath.Join(workspaceDir, "main.tf"), "resource {}")

	if err := wd.DeleteForWorkspace(logging.NewNoopLogger(t), repo, pull, "my-workspace"); err != nil {
		t.Fatalf("DeleteForWorkspace refused an ordinary workspace: %v", err)
	}
	mustNotExist(t, workspaceDir)
}

func TestFunc_WorkingDir_LocateOrdinaryDirectories(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 3, BaseRepo: repo}
	workspaceDir := filepath.Join(dataDir, "repos", "owner", "repo", "3", "my-workspace")
	mkdir(t, workspaceDir)

	got, err := wd.GetWorkingDir(repo, pull, "my-workspace")
	if err != nil {
		t.Fatalf("GetWorkingDir refused an ordinary workspace: %v", err)
	}
	if got != workspaceDir {
		t.Fatalf("GetWorkingDir returned %q, want %q", got, workspaceDir)
	}

	pullDir, err := wd.GetPullDir(repo, pull)
	if err != nil {
		t.Fatalf("GetPullDir refused an ordinary pull request: %v", err)
	}
	if pullDir != filepath.Dir(workspaceDir) {
		t.Fatalf("GetPullDir returned %q, want %q", pullDir, filepath.Dir(workspaceDir))
	}
}
