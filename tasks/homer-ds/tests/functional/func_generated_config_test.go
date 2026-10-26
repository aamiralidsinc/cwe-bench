// Functional test: a configuration produced by the product's generator must remain usable
// as-is: starting from it with no operator-supplied credential still yields a working
// installation with an administrator credential.
package hiddentests

import (
	"path/filepath"
	"testing"

	"github.com/sipcapture/homer-core/src/cli"
)

func TestFunc_WizardPresetConfigStartsUsably(t *testing.T) {
	dir := t.TempDir()
	generated := filepath.Join(dir, "generated.json")
	if err := cli.RunWizardCmd(cli.WizardFlags{Profile: "all-in-one", Output: generated}); err != nil {
		t.Fatalf("the configuration generator failed: %v", err)
	}
	settingsDB := filepath.Join(dir, "settings.duckdb")
	c, _ := startCoordinator(t, generated, settingsDB) // waits for the health endpoint
	_ = c.Stop()

	if stored := storedCredential(t, settingsDB, "admin"); stored == "" {
		t.Fatalf("starting from a generated configuration left no administrator credential")
	}
}
