// Security test: the startup repair path for an existing administrator row whose stored
// credential is missing must not fill it with the documented default.
package hiddentests

import (
	"path/filepath"
	"testing"
)

func TestSec_EmptyExistingRowIsNotRepairedWithDefault(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	createSettingsDB(t, settingsDB)
	seedUser(t, settingsDB, "admin", "")

	cfgPath := writeCoordinatorConfig(t, dir, `{"type":"internal"}`, settingsDB)
	_, port := startCoordinator(t, cfgPath, settingsDB)

	assertCredentialRejected(t, port, "admin", documentedDefaultPassword,
		"a repaired administrator row")

	stored := storedCredential(t, settingsDB, "admin")
	if stored == "" {
		t.Fatalf("the administrator row was left without a credential")
	}
	if passwordMatches(documentedDefaultPassword, stored) {
		t.Fatalf("the administrator row was repaired with the documented default")
	}
}
