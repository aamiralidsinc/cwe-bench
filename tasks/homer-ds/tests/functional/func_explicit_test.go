// Functional tests: credentials the operator supplies explicitly must keep working and
// must not be replaced.
package hiddentests

import (
	"fmt"
	"path/filepath"
	"testing"
)

func TestFunc_ExplicitBcryptCredentialLogsIn(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	pw := "operator-chosen-Bcrypt-9f3a"
	hash := bcryptOf(t, pw)
	auth := fmt.Sprintf(`{"type":"internal","admin_password_hash":%q}`, hash)
	cfgPath := writeCoordinatorConfig(t, dir, auth, settingsDB)

	c, port := startCoordinator(t, cfgPath, settingsDB)
	code, token := login(t, port, "admin", pw)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("the operator's explicit credential was not accepted (status %d)", code)
	}
	assertCredentialRejected(t, port, "admin", "not-the-operator-password", "a wrong password")
	_ = c.Stop()

	if stored := storedCredential(t, settingsDB, "admin"); stored != hash {
		t.Fatalf("the operator's explicit credential was replaced")
	}
}

func TestFunc_ExplicitLegacyCredentialLogsIn(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	pw := "operator-chosen-Legacy-3c1b"
	hash := sha256Hex(pw)
	auth := fmt.Sprintf(`{"type":"internal","admin_password_hash":%q}`, hash)
	cfgPath := writeCoordinatorConfig(t, dir, auth, settingsDB)

	c, port := startCoordinator(t, cfgPath, settingsDB)
	code, token := login(t, port, "admin", pw)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("the operator's explicit legacy credential was not accepted (status %d)", code)
	}
	_ = c.Stop()

	if stored := storedCredential(t, settingsDB, "admin"); stored != hash {
		t.Fatalf("the operator's explicit legacy credential was replaced")
	}
}
