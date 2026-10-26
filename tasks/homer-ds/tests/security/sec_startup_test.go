// Security tests: a deployment that selects the built-in sign-in provider without an
// operator-supplied administrator credential must never end up with the credential the
// product has historically shipped. Each test drives the real configuration loader and
// the real coordinator startup, then tries the documented default password. It never
// asserts a particular refusal status: any non-authenticating outcome is a pass.
package hiddentests

import (
	"path/filepath"
	"testing"
)

func assertNoFixedCredential(t *testing.T, authJSON string) {
	t.Helper()
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	cfgPath := writeCoordinatorConfig(t, dir, authJSON, settingsDB)
	_, port := startCoordinator(t, cfgPath, settingsDB)

	assertCredentialRejected(t, port, "admin", documentedDefaultPassword,
		"a deployment with no operator-supplied credential")

	stored := storedCredential(t, settingsDB, "admin")
	if stored == "" {
		t.Fatalf("no administrator credential was issued")
	}
	if passwordMatches(documentedDefaultPassword, stored) {
		t.Fatalf("the stored administrator credential is the documented default")
	}
}

func TestSec_StartupStringFormDoesNotUseDefault(t *testing.T) {
	assertNoFixedCredential(t, `"internal"`)
}

func TestSec_StartupObjectFormDoesNotUseDefault(t *testing.T) {
	assertNoFixedCredential(t, `{"type":"internal"}`)
}

func TestSec_StartupOmittedAuthDoesNotUseDefault(t *testing.T) {
	assertNoFixedCredential(t, `OMIT`)
}

func TestSec_StartupBlankHashDoesNotUseDefault(t *testing.T) {
	assertNoFixedCredential(t, `{"type":"internal","admin_password_hash":"   "}`)
}
