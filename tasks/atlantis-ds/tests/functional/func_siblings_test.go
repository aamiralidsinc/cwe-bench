package vtesting

import (
	"testing"

	"github.com/hashicorp/go-version"
	"github.com/runatlantis/atlantis/server/core/config/valid"
	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/command"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
	tally "github.com/uber-go/tally/v4"
)

// An ordinary project name whose artifacts stay inside the workspace, and the
// ordinary flow of preparing a plan command, must keep working.

func TestFunc_PlanArtifact_OrdinaryProjectName(t *testing.T) {
	repoDir := t.TempDir()
	ver := version.Must(version.NewVersion("1.5.0"))
	runner, _ := planSnapshotRunner(t, repoDir)
	ctx := projectContext(t, "default", ".", "my-project", []valid.Step{{StepName: "plan"}})
	ctx.TerraformVersion = ver
	ctx.CommandName = command.Plan

	if err := runner.Plan(ctx).Error; err != nil {
		t.Fatalf("Plan failed for an ordinary project name: %v", err)
	}
}

func TestFunc_ContextBuild_OrdinaryProjectDirectory(t *testing.T) {
	repoDir := t.TempDir()
	ver := version.Must(version.NewVersion("1.5.0"))
	builder := &events.DefaultProjectCommandContextBuilder{CommentBuilder: &fakeCommentBuilder{}}
	prjCfg := valid.MergedProjectCfg{
		RepoRelDir:       "modules/vpc",
		Workspace:        "default",
		TerraformVersion: ver,
	}
	ctx := &command.Context{
		Log:      logging.NewNoopLogger(t),
		Pull:     models.PullRequest{Num: 1, BaseRepo: models.Repo{FullName: "owner/repo"}},
		HeadRepo: models.Repo{FullName: "owner/repo"},
		Scope:    tally.NewTestScope("", nil),
	}

	built := builder.BuildProjectContext(ctx, command.Plan, "", prjCfg, nil, repoDir,
		false, false, false, false, false, &fakeTerraform{detected: ver})

	if len(built) != 1 {
		t.Fatalf("built %d project contexts, want 1", len(built))
	}
	if built[0].RepoRelDir != "modules/vpc" {
		t.Fatalf("project context has dir %q, want modules/vpc", built[0].RepoRelDir)
	}
}
