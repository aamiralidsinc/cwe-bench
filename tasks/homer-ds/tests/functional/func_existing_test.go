// Functional tests: existing administrator rows must keep working untouched, in either
// stored form.
package hiddentests

import (
	"path/filepath"
	"testing"
)

func TestFunc_ExistingStoredCredentialNotOverwritten(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	createSettingsDB(t, settingsDB)
	pw := "already-stored-Bcrypt-51be"
	seed := bcryptOf(t, pw)
	seedUser(t, settingsDB, "admin", seed)

	cfgPath := writeCoordinatorConfig(t, dir, `{"type":"internal"}`, settingsDB)
	c, port := startCoordinator(t, cfgPath, settingsDB)
	code, token := login(t, port, "admin", pw)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("an existing administrator credential stopped working (status %d)", code)
	}
	_ = c.Stop()

	if stored := storedCredential(t, settingsDB, "admin"); stored != seed {
		t.Fatalf("an existing administrator credential was overwritten at startup")
	}
}

func TestFunc_LegacyStoredCredentialAuthenticates(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	createSettingsDB(t, settingsDB)
	pw := "migrated-Legacy-2d90"
	seed := sha256Hex(pw)
	seedUser(t, settingsDB, "admin", seed)

	cfgPath := writeCoordinatorConfig(t, dir, `{"type":"internal"}`, settingsDB)
	c, port := startCoordinator(t, cfgPath, settingsDB)
	code, token := login(t, port, "admin", pw)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("a migrated legacy credential stopped authenticating (status %d)", code)
	}
	_ = c.Stop()

	if stored := storedCredential(t, settingsDB, "admin"); stored != seed {
		t.Fatalf("a migrated legacy credential was overwritten at startup")
	}
}
