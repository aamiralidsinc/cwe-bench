// Functional tests: a blank effective credential still yields a usable installation, and
// the repair command keeps honouring an explicitly supplied credential.
package hiddentests

import (
	"fmt"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sipcapture/homer-core/src/cli"
)

func TestFunc_BlankHashStillBootstrapsUsable(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	cfgPath := writeCoordinatorConfig(t, dir, `{"type":"internal","admin_password_hash":"  \t "}`, settingsDB)

	c, _ := startCoordinator(t, cfgPath, settingsDB)
	_ = c.Stop()

	stored := storedCredential(t, settingsDB, "admin")
	if strings.TrimSpace(stored) == "" {
		t.Fatalf("a blank credential left the installation without an administrator")
	}
	if stored != strings.TrimSpace(stored) {
		t.Fatalf("the stored administrator credential is blank or padded")
	}
}

func TestFunc_ResetAdminExplicitHashStillWorks(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	createSettingsDB(t, settingsDB)
	pw := "recovery-chosen-Legacy-6f02"
	hash := sha256Hex(pw)
	auth := fmt.Sprintf(`{"type":"internal","admin_password_hash":%q}`, hash)
	cfgPath := writeCoordinatorConfig(t, dir, auth, settingsDB)

	if err := cli.RunResetAdminPassword(cfgPath); err != nil {
		t.Fatalf("the repair command refused an explicitly supplied credential: %v", err)
	}
	if stored := storedCredential(t, settingsDB, "admin"); stored != hash {
		t.Fatalf("the repair command did not apply the explicitly supplied credential")
	}
}
