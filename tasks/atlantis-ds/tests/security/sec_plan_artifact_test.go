package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/hashicorp/go-version"
	"github.com/runatlantis/atlantis/server/core/config/valid"
	"github.com/runatlantis/atlantis/server/core/runtime"
	"github.com/runatlantis/atlantis/server/core/terraform"
	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/command"
)

// The plan step runner records an artifact under a directory named after the
// project. A project name that resolves outside the workspace clone must not
// create anything there, whether the name arrived with the request or was
// stored in repository configuration.

func planSnapshotRunner(t *testing.T, repoDir string) (*events.DefaultProjectCommandRunner, *markerStep) {
	t.Helper()
	ver := version.Must(version.NewVersion("1.5.0"))
	planStep := runtime.NewPlanStepRunner(&fakeTerraform{}, terraform.NewDistribution("terraform"), ver, nil, nil)
	runner, step := newRunners(t, repoDir)
	runner.PlanStepRunner = planStep
	return runner, step
}

func TestSec_PlanArtifact_ProjectNameEscape(t *testing.T) {
	repoDir := t.TempDir()
	// The artifact directory is built from the workspace clone and the project
	// name; pick a name that resolves onto a fresh directory outside it.
	victim := filepath.Join(t.TempDir(), "artifact-target")
	base := filepath.Join(repoDir, ".atlantis", "plan-output")
	name := relTo(t, base, victim)

	ver := version.Must(version.NewVersion("1.5.0"))
	runner, _ := planSnapshotRunner(t, repoDir)
	ctx := projectContext(t, "default", ".", name, []valid.Step{{StepName: "plan"}})
	ctx.TerraformVersion = ver
	ctx.CommandName = command.Plan

	_ = runner.Plan(ctx) // the command may succeed; it must not write outside

	mustNotExist(t, filepath.Join(victim, "output.txt"))
	mustNotExist(t, victim)
}
