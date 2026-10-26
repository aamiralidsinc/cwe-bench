// Package vtesting holds the hidden behavioural tests for the atlantis-ds task.
//
// Every test drives product code directly: the working-directory implementation
// and the per-command runners the server's HTTP handlers call. Nothing here
// starts a web server, reaches the network or shells out to terraform; the
// command steps are replaced with a runner that drops a harmless marker file in
// the directory the server is about to operate in.
package vtesting

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/hashicorp/go-version"
	"github.com/runatlantis/atlantis/server/core/config/valid"
	"github.com/runatlantis/atlantis/server/core/locking"
	"github.com/runatlantis/atlantis/server/core/runtime"
	"github.com/runatlantis/atlantis/server/core/terraform"
	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/command"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/events/webhooks"
	"github.com/runatlantis/atlantis/server/logging"
	tally "github.com/uber-go/tally/v4"
)

// ---------- filesystem helpers (expected values are computed here) ----------

func mkdir(t *testing.T, p string) {
	t.Helper()
	if err := os.MkdirAll(p, 0700); err != nil {
		t.Fatalf("mkdir %s: %v", p, err)
	}
}

func writeFile(t *testing.T, p, body string) {
	t.Helper()
	mkdir(t, filepath.Dir(p))
	if err := os.WriteFile(p, []byte(body), 0600); err != nil {
		t.Fatalf("write %s: %v", p, err)
	}
}

func exists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

func mustExist(t *testing.T, p string) {
	t.Helper()
	if !exists(p) {
		t.Fatalf("%s was removed or never created", p)
	}
}

func mustNotExist(t *testing.T, p string) {
	t.Helper()
	if exists(p) {
		t.Fatalf("%s was created", p)
	}
}

func relTo(t *testing.T, from, to string) string {
	t.Helper()
	r, err := filepath.Rel(from, to)
	if err != nil {
		t.Fatalf("rel %s -> %s: %v", from, to, err)
	}
	return filepath.ToSlash(r)
}

// ---------- product doubles ----------

type fakeWorkingDir struct {
	events.WorkingDir
	repoDir string
}

func (f *fakeWorkingDir) Clone(logging.SimpleLogging, models.Repo, models.PullRequest, string) (string, error) {
	return f.repoDir, nil
}

func (f *fakeWorkingDir) MergeAgain(logging.SimpleLogging, models.Repo, models.PullRequest, string) (bool, error) {
	return false, nil
}

func (f *fakeWorkingDir) GetWorkingDir(models.Repo, models.PullRequest, string) (string, error) {
	return f.repoDir, nil
}

func (f *fakeWorkingDir) GitReadLock(models.Repo, models.PullRequest, string) func() {
	return func() {}
}

type fakeProjectLocker struct {
	events.ProjectLocker
}

func (f *fakeProjectLocker) TryLock(logging.SimpleLogging, models.PullRequest, models.User, string, models.Project, bool) (*events.TryLockResponse, error) {
	return &events.TryLockResponse{LockAcquired: true, LockKey: "lock-key", UnlockFn: func() error { return nil }}, nil
}

type fakeWorkingDirLocker struct {
	events.WorkingDirLocker
}

func (f *fakeWorkingDirLocker) TryLock(string, int, string, string, string, command.Name) (func(), error) {
	return func() {}, nil
}

type fakeRequirementHandler struct {
	events.CommandRequirementHandler
}

func (f *fakeRequirementHandler) ValidatePlanProject(string, command.ProjectContext) (string, error) {
	return "", nil
}
func (f *fakeRequirementHandler) ValidateApplyProject(string, command.ProjectContext) (string, error) {
	return "", nil
}
func (f *fakeRequirementHandler) ValidateImportProject(string, command.ProjectContext) (string, error) {
	return "", nil
}
func (f *fakeRequirementHandler) ValidateProjectDependencies(command.ProjectContext) (string, error) {
	return "", nil
}

// markerStep stands in for a terraform step: it records the directory the
// server was about to run in by dropping a marker file there.
type markerStep struct {
	events.StepRunner
	name string
}

func (m *markerStep) Run(_ command.ProjectContext, _ []string, path string, _ map[string]string) (string, error) {
	return "", os.WriteFile(filepath.Join(path, m.name), []byte("step ran here"), 0600)
}

type fakeWebhooks struct {
	events.WebhooksSender
}

func (f *fakeWebhooks) Send(logging.SimpleLogging, webhooks.ApplyResult) error { return nil }

type fakeLockURLGenerator struct {
	events.LockURLGenerator
}

func (f *fakeLockURLGenerator) GenerateLockURL(string) string { return "https://example.invalid/lock" }

type fakeCommentBuilder struct {
	events.CommentBuilder
}

func (f *fakeCommentBuilder) BuildPlanComment(string, string, string, []string) string { return "plan" }
func (f *fakeCommentBuilder) BuildApplyComment(string, string, string, bool, string) string {
	return "apply"
}
func (f *fakeCommentBuilder) BuildApprovePoliciesComment(string, string, string) string {
	return "approve"
}

type fakeTerraform struct {
	runtime.TerraformExec
	detected *version.Version
}

func (f *fakeTerraform) RunCommandWithVersion(command.ProjectContext, string, []string, map[string]string, terraform.Distribution, *version.Version, string) (string, error) {
	return "Plan: 0 to add, 0 to change, 0 to destroy.\n", nil
}

func (f *fakeTerraform) EnsureVersion(logging.SimpleLogging, terraform.Distribution, *version.Version) error {
	return nil
}

func (f *fakeTerraform) DetectVersion(logging.SimpleLogging, string) *version.Version {
	return f.detected
}

// fakeUnlocker answers lock-store reads from a fixed value, like the lock
// database would when a saved lock is deleted.
type fakeUnlocker struct {
	locking.Locker
	lock  models.ProjectLock
	locks []models.ProjectLock
}

func (f *fakeUnlocker) Unlock(string) (*models.ProjectLock, error) {
	return &f.lock, nil
}

func (f *fakeUnlocker) UnlockByPull(string, int) ([]models.ProjectLock, error) {
	return f.locks, nil
}

// ---------- runners ----------

func newRunners(t *testing.T, repoDir string) (*events.DefaultProjectCommandRunner, *markerStep) {
	t.Helper()
	step := &markerStep{name: "step-marker"}
	return &events.DefaultProjectCommandRunner{
		Locker:                    &fakeProjectLocker{},
		LockURLGenerator:          &fakeLockURLGenerator{},
		WorkingDir:                &fakeWorkingDir{repoDir: repoDir},
		WorkingDirLocker:          &fakeWorkingDirLocker{},
		CommandRequirementHandler: &fakeRequirementHandler{},
		Webhooks:                  &fakeWebhooks{},
		InitStepRunner:            step,
		PlanStepRunner:            step,
		ApplyStepRunner:           step,
		VersionStepRunner:         step,
		ImportStepRunner:          step,
		StateRmStepRunner:         step,
		PolicyCheckStepRunner:     step,
	}, step
}

func projectContext(t *testing.T, workspace, repoRelDir, projectName string, steps []valid.Step) command.ProjectContext {
	t.Helper()
	repo := models.Repo{FullName: "owner/repo", Owner: "owner", Name: "repo"}
	pull := models.PullRequest{Num: 1, BaseRepo: repo, HeadBranch: "feature", BaseBranch: "main", HeadCommit: "deadbeef"}
	return command.ProjectContext{
		Log:         logging.NewNoopLogger(t),
		Pull:        pull,
		HeadRepo:    repo,
		BaseRepo:    repo,
		Workspace:   workspace,
		RepoRelDir:  repoRelDir,
		ProjectName: projectName,
		Steps:       steps,
		Scope:       tally.NewTestScope("", nil),
	}
}

func initStep() []valid.Step { return []valid.Step{{StepName: "init"}} }
