// Security test: the credential-repair command, run because the effective configuration
// supplies no administrator credential, must not fall back to the documented default.
package hiddentests

import (
	"path/filepath"
	"testing"

	"github.com/sipcapture/homer-core/src/cli"
)

func TestSec_ResetAdminDoesNotInstallDefault(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	createSettingsDB(t, settingsDB)
	cfgPath := writeCoordinatorConfig(t, dir, `{"type":"internal"}`, settingsDB)

	// The command may refuse; that is a valid outcome. What it must not do is leave a
	// fixed administrator credential behind.
	_ = cli.RunResetAdminPassword(cfgPath)

	if stored := storedCredential(t, settingsDB, "admin"); stored != "" && passwordMatches(documentedDefaultPassword, stored) {
		t.Fatalf("the repair command installed the documented default credential")
	}
}
