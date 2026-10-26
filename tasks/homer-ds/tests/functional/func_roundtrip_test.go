// Functional tests: an explicit administrator credential must survive the product's own
// write-out and re-read of the configuration.
package hiddentests

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/sipcapture/homer-core/src/config"
)

// writeRoundTripConfig serialises a configuration through the product's own encoder,
// writes it, and returns the file path.
func writeRoundTripConfig(t *testing.T, dir, storedHash string) string {
	t.Helper()
	var cfg config.Config
	cfg.Coordinator.Enable = true
	cfg.Coordinator.Auth = config.AuthConfig{
		Type:              "internal",
		AdminUser:         "admin",
		AdminPasswordHash: storedHash,
	}
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		t.Fatalf("writing the configuration failed: %v", err)
	}
	path := filepath.Join(dir, "roundtrip.json")
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatalf("write: %v", err)
	}
	return path
}

func TestFunc_ExplicitDefaultHashSurvivesSaveReload(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	// Operators of the shipped container examples configure exactly this credential.
	path := writeRoundTripConfig(t, dir, sha256Hex(documentedDefaultPassword))

	c, port := startCoordinator(t, path, settingsDB)
	code, token := login(t, port, "admin", documentedDefaultPassword)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("an explicitly configured credential stopped working after write-out and re-read (status %d)", code)
	}
	_ = c.Stop()
}

func TestFunc_BcryptHashSurvivesSaveReload(t *testing.T) {
	dir := t.TempDir()
	settingsDB := filepath.Join(dir, "settings.duckdb")
	pw := "roundtrip-Bcrypt-77aa"
	hash := bcryptOf(t, pw)
	path := writeRoundTripConfig(t, dir, hash)

	c, port := startCoordinator(t, path, settingsDB)
	code, token := login(t, port, "admin", pw)
	if token == "" || code < 200 || code >= 300 {
		t.Fatalf("an explicitly configured credential stopped working after write-out and re-read (status %d)", code)
	}
	_ = c.Stop()
	if stored := storedCredential(t, settingsDB, "admin"); stored != hash {
		t.Fatalf("the round-tripped credential was altered")
	}
}
