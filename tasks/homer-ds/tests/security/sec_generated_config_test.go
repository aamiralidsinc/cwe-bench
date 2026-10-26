// Security tests: a configuration file the product itself generates is applied later by
// the same loader and startup path. If that generated file carries a fixed administrator
// credential, the deployment that uses it is vulnerable even though the loader no longer
// invents one.
package hiddentests

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/sipcapture/homer-core/src/cli"
)

func TestSec_WizardPresetConfigDoesNotCarryDefault(t *testing.T) {
	dir := t.TempDir()
	generated := filepath.Join(dir, "generated.json")
	if err := cli.RunWizardCmd(cli.WizardFlags{Profile: "all-in-one", Output: generated}); err != nil {
		t.Fatalf("the configuration generator failed: %v", err)
	}
	if _, err := os.Stat(generated); err != nil {
		t.Fatalf("the configuration generator wrote no file: %v", err)
	}
	settingsDB := filepath.Join(dir, "settings.duckdb")
	_, port := startCoordinator(t, generated, settingsDB)

	assertCredentialRejected(t, port, "admin", documentedDefaultPassword,
		"a deployment using a generated configuration")
}

func TestSec_ExampleConfigDoesNotCarryDefault(t *testing.T) {
	dir := t.TempDir()
	old, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	defer func() { _ = os.Chdir(old) }()
	if err := cli.RunSystemCmd(cli.SystemFlags{GenerateExampleConfig: true}); err != nil {
		t.Fatalf("the example configuration generator failed: %v", err)
	}
	generated := filepath.Join(dir, "homer-core-example.json")
	if _, err := os.Stat(generated); err != nil {
		t.Fatalf("the example configuration was not written: %v", err)
	}
	settingsDB := filepath.Join(dir, "settings.duckdb")
	_, port := startCoordinator(t, generated, settingsDB)

	assertCredentialRejected(t, port, "admin", documentedDefaultPassword,
		"a deployment using an example configuration")
}
