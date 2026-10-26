package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/hashicorp/go-version"
	"github.com/runatlantis/atlantis/server/core/config/valid"
	"github.com/runatlantis/atlantis/server/events"
	"github.com/runatlantis/atlantis/server/events/command"
	"github.com/runatlantis/atlantis/server/events/models"
	"github.com/runatlantis/atlantis/server/logging"
	tally "github.com/uber-go/tally/v4"
)

// While a plan command is being prepared, the server discards the previous
// plan for the project. The project directory used for that work must not
// resolve outside the workspace clone: preparation happens before any command
// step and must not touch an outside location.

func TestSec_ContextBuild_StalePlanEscape(t *testing.T) {
	repoDir := t.TempDir()
	victimDir := filepath.Join(t.TempDir(), "victim")
	mkdir(t, victimDir)
	stalePlan := filepath.Join(victimDir, "default.tfplan")
	writeFile(t, stalePlan, "previous plan")

	ver := version.Must(version.NewVersion("1.5.0"))
	builder := &events.DefaultProjectCommandContextBuilder{CommentBuilder: &fakeCommentBuilder{}}
	prjCfg := valid.MergedProjectCfg{
		RepoRelDir:       relTo(t, repoDir, victimDir),
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

	if len(built) == 0 {
		t.Fatalf("no project context was built for a legitimate project configuration")
	}
	mustExist(t, stalePlan)
}
