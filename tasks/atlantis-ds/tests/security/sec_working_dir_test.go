package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
)

// The working-directory implementation keeps each pull request's data directly
// below its managed data directory. A repository identity or workspace name
// that walks out of its slot must be refused and must not delete or expose the
// directory it resolves to.

func TestSec_WorkingDir_DeleteRepoIdentityEscape(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	outside := filepath.Join(t.TempDir(), "outside")
	victim := filepath.Join(outside, "1")
	mkdir(t, victim)
	sentinel := filepath.Join(victim, "keep")
	writeFile(t, sentinel, "keep me")

	repo := models.Repo{FullName: relTo(t, filepath.Join(dataDir, "repos"), outside)}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	err := wd.Delete(logging.NewNoopLogger(t), repo, pull)
	if err == nil {
		t.Fatalf("Delete accepted a repository identity that resolves outside the managed data directory")
	}
	mustExist(t, sentinel)
}

func TestSec_WorkingDir_DeleteForWorkspaceEscape(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	// Another pull request of the same repository.
	victim := filepath.Join(dataDir, "repos", "owner", "repo", "2")
	mkdir(t, victim)
	sentinel := filepath.Join(victim, "keep")
	writeFile(t, sentinel, "keep me")

	err := wd.DeleteForWorkspace(logging.NewNoopLogger(t), repo, pull, "../2")
	if err == nil {
		t.Fatalf("DeleteForWorkspace accepted a workspace that resolves to another pull request's directory")
	}
	mustExist(t, sentinel)
}

func TestSec_WorkingDir_GetPullDirRepoIdentityEscape(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	outside := filepath.Join(t.TempDir(), "outside")
	mkdir(t, filepath.Join(outside, "1"))

	repo := models.Repo{FullName: relTo(t, filepath.Join(dataDir, "repos"), outside)}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	got, err := wd.GetPullDir(repo, pull)
	if err == nil {
		t.Fatalf("GetPullDir returned %q for a repository identity outside the managed data directory", got)
	}
}

func TestSec_WorkingDir_GetWorkingDirWorkspaceEscape(t *testing.T) {
	dataDir := t.TempDir()
	wd := &events.FileWorkspace{DataDir: dataDir}

	repo := models.Repo{FullName: "owner/repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo}

	// Another workspace directory of the same repository, reachable with "..".
	other := filepath.Join(dataDir, "repos", "owner", "repo", "other")
	mkdir(t, other)

	got, err := wd.GetWorkingDir(repo, pull, "../other")
	if err == nil {
		t.Fatalf("GetWorkingDir returned %q for a workspace that resolves outside its own directory", got)
	}
}
