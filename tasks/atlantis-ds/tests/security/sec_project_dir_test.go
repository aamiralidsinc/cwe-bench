package vtesting

import (
	"path/filepath"
	"testing"
)

// A project's directory relative to the checkout names the directory its
// command steps run in. A value that resolves outside the workspace clone must
// be refused before any step runs.

func attackLayout(t *testing.T, withSibling bool) (repoDir, outside, target string, rel string) {
	t.Helper()
	repoDir = t.TempDir()
	outside = filepath.Join(t.TempDir(), "outside")
	mkdir(t, outside)
	if withSibling {
		// exercise a path that leaves the workspace but stays inside the pull
		// directory, with an embedded separator component before the ".."s
		parent := filepath.Dir(repoDir)
		sibling := filepath.Join(parent, "sibling-workspace")
		mkdir(t, sibling)
		rel = "../sibling-workspace"
		if filepath.Join(repoDir, rel) != sibling {
			t.Fatalf("bad test layout: %s resolves to %s", rel, filepath.Join(repoDir, rel))
		}
		return repoDir, parent, sibling, rel
	}
	rel = relTo(t, repoDir, outside)
	if filepath.Join(repoDir, rel) != outside {
		t.Fatalf("bad test layout: %s resolves to %s", rel, filepath.Join(repoDir, rel))
	}
	return repoDir, outside, outside, rel
}

// embeddedTraversal spells the same target with a real component before the
// upward steps, the way a client might write "from here, up and out".
func embeddedTraversal(t *testing.T, repoDir, rel, target string) string {
	t.Helper()
	spelled := "nested/.." + string(filepath.Separator) + rel
	if filepath.Join(repoDir, spelled) != target {
		t.Fatalf("bad test layout: %s resolves to %s, want %s", spelled, filepath.Join(repoDir, spelled), target)
	}
	return spelled
}

func assertNoStep(t *testing.T, err error, marker string) {
	t.Helper()
	if err == nil {
		t.Fatalf("the command ran a step for a project directory outside the workspace")
	}
	mustNotExist(t, marker)
}

func TestSec_ProjectDir_PlanEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", rel, "", initStep())

	assertNoStep(t, runner.Plan(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_ApplyEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	prefixed := embeddedTraversal(t, repoDir, rel, outside)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", prefixed, "", initStep())

	assertNoStep(t, runner.Apply(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_PolicyCheckEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", rel, "", initStep())

	assertNoStep(t, runner.PolicyCheck(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_VersionEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	prefixed := embeddedTraversal(t, repoDir, rel, outside)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", prefixed, "", initStep())

	assertNoStep(t, runner.Version(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_ImportEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", rel, "", initStep())

	assertNoStep(t, runner.Import(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_StateRmEscape(t *testing.T) {
	repoDir, _, outside, rel := attackLayout(t, false)
	prefixed := embeddedTraversal(t, repoDir, rel, outside)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", prefixed, "", initStep())

	assertNoStep(t, runner.StateRm(ctx).Error, filepath.Join(outside, step.name))
}

func TestSec_ProjectDir_PlanCrossWorkspaceEscape(t *testing.T) {
	repoDir, _, sibling, rel := attackLayout(t, true)
	runner, step := newRunners(t, repoDir)
	ctx := projectContext(t, "default", rel, "", initStep())

	assertNoStep(t, runner.Plan(ctx).Error, filepath.Join(sibling, step.name))
}
