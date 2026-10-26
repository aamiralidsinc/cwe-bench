// Hidden test support helpers (copied into the module at grading time).
package hiddentests

import (
	"bytes"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	_ "github.com/duckdb/duckdb-go/v2"
	"golang.org/x/crypto/bcrypt"

	"github.com/sipcapture/homer-core/src/config"
	"github.com/sipcapture/homer-core/src/coordinator"
)

// documentedDefaultPassword is the well-known bootstrap password the product has
// historically shipped. It is the marker the security tests use, never a live secret.
const documentedDefaultPassword = "sipcapture"

// sha256Hex computes the legacy stored form in the test itself.
func sha256Hex(s string) string {
	sum := sha256.Sum256([]byte(s))
	return hex.EncodeToString(sum[:])
}

// bcryptOf computes a bcrypt hash in the test itself.
func bcryptOf(t *testing.T, pw string) string {
	t.Helper()
	b, err := bcrypt.GenerateFromPassword([]byte(pw), bcrypt.DefaultCost)
	if err != nil {
		t.Fatalf("bcrypt: %v", err)
	}
	return string(b)
}

// passwordMatches checks a password against either stored form the product supports,
// using only the test's own implementation.
func passwordMatches(pw, stored string) bool {
	stored = strings.TrimSpace(stored)
	if stored == "" {
		return false
	}
	if strings.HasPrefix(stored, "$2a$") || strings.HasPrefix(stored, "$2b$") || strings.HasPrefix(stored, "$2y$") {
		return bcrypt.CompareHashAndPassword([]byte(stored), []byte(pw)) == nil
	}
	return strings.EqualFold(sha256Hex(pw), stored)
}

func freePort(t *testing.T) int {
	t.Helper()
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("free port: %v", err)
	}
	defer l.Close()
	return l.Addr().(*net.TCPAddr).Port
}

// writeCoordinatorConfig writes a configuration file whose coordinator section selects
// built-in sign-in. authJSON is the raw JSON value of coordinator.auth; pass "OMIT" to
// leave the auth key out entirely. settingsPath is written into the file but the
// coordinator helpers also retarget it at start time.
func writeCoordinatorConfig(t *testing.T, dir, authJSON, settingsPath string) string {
	t.Helper()
	coord := map[string]any{
		"enable":           true,
		"http_server":      map[string]any{"enable": true, "host": "127.0.0.1", "port": 0},
		"settings_db_path": settingsPath,
		"jwt":              map[string]any{"secret": "hidden-test-signing-secret-0123456789"},
	}
	if authJSON != "OMIT" {
		coord["auth"] = json.RawMessage(authJSON)
	}
	doc := map[string]any{"coordinator": coord}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		t.Fatalf("marshal config: %v", err)
	}
	path := filepath.Join(dir, "homer.json")
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}
	return path
}

// startCoordinator loads cfgPath with the real loader, points its settings database and
// HTTP listener at the test's temporary directory, then starts the real coordinator.
// It fails the test if the deployment cannot be brought up: an installation with no
// operator-supplied credential must remain usable.
func startCoordinator(t *testing.T, cfgPath, settingsPath string) (*coordinator.Coordinator, int) {
	t.Helper()
	// Take the test's handle on the settings database before the product opens it, so the
	// product's open/close cycle never leaves the instance cache empty for this path.
	openStore(t, settingsPath)
	cfg, err := config.Load(cfgPath)
	if err != nil {
		t.Fatalf("loading the configuration failed: %v", err)
	}
	port := freePort(t)
	cfg.Coordinator.SettingsDBPath = settingsPath
	cfg.Coordinator.HTTPServer.Host = "127.0.0.1"
	cfg.Coordinator.HTTPServer.Port = port
	cfg.Coordinator.HTTPServer.Enable = true
	cfg.Coordinator.Nodes = nil

	c, err := coordinator.New(&cfg.Coordinator)
	if err != nil {
		t.Fatalf("starting the coordinator failed: %v", err)
	}
	if err := c.Start(); err != nil {
		t.Fatalf("starting the coordinator failed: %v", err)
	}
	t.Cleanup(func() { _ = c.Stop() })
	waitHealthy(t, port)
	return c, port
}

func waitHealthy(t *testing.T, port int) {
	t.Helper()
	client := &http.Client{Timeout: 2 * time.Second}
	url := fmt.Sprintf("http://127.0.0.1:%d/api/v3/health", port)
	deadline := time.Now().Add(10 * time.Second)
	for time.Now().Before(deadline) {
		resp, err := client.Get(url)
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return
			}
		}
		time.Sleep(25 * time.Millisecond)
	}
	t.Fatalf("the coordinator did not become ready")
}

// login performs the product's password sign-in for the built-in provider.
func login(t *testing.T, port int, user, pass string) (int, string) {
	t.Helper()
	body, _ := json.Marshal(map[string]string{"username": user, "password": pass})
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(fmt.Sprintf("http://127.0.0.1:%d/api/v3/auth", port),
		"application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatalf("sign-in request failed: %v", err)
	}
	defer resp.Body.Close()
	var out struct {
		Success bool `json:"success"`
		Data    struct {
			Token string `json:"token"`
		} `json:"data"`
	}
	_ = json.NewDecoder(resp.Body).Decode(&out)
	return resp.StatusCode, out.Data.Token
}

// assertCredentialRejected fails unless signing in with the credential is refused.
func assertCredentialRejected(t *testing.T, port int, user, pass, why string) {
	t.Helper()
	code, token := login(t, port, user, pass)
	if token != "" || (code >= 200 && code < 300) {
		t.Fatalf("%s: the credential was accepted (status %d)", why, code)
	}
}

// The settings database is opened through DuckDB's process-wide instance cache. Opening and
// closing the same path repeatedly races with the cache in the driver, so a test opens (or
// inherits) one handle and keeps it until the test ends; the product's own handles share the
// same instance.
var (
	storeMu sync.Mutex
	stores  = map[string]*sql.DB{}
)

func openStore(t *testing.T, path string) *sql.DB {
	t.Helper()
	storeMu.Lock()
	defer storeMu.Unlock()
	if db, ok := stores[path]; ok {
		return db
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	db, err := sql.Open("duckdb", path)
	if err != nil {
		t.Fatalf("open settings db: %v", err)
	}
	if err := db.Ping(); err != nil {
		t.Fatalf("open settings db: %v", err)
	}
	stores[path] = db
	t.Cleanup(func() {
		storeMu.Lock()
		delete(stores, path)
		storeMu.Unlock()
		_ = db.Close()
	})
	return db
}

// createSettingsDB opens the test's settings database and creates the schema the product
// expects before the coordinator opens it (test-side bookkeeping, no product helper).
func createSettingsDB(t *testing.T, path string) {
	t.Helper()
	db := openStore(t, path)
	stmts := []string{
		`CREATE SEQUENCE IF NOT EXISTS users_id_seq`,
		`CREATE TABLE IF NOT EXISTS users (
			id BIGINT PRIMARY KEY DEFAULT nextval('users_id_seq'),
			username VARCHAR,
			password_hash VARCHAR,
			email VARCHAR,
			full_name VARCHAR,
			is_admin BOOLEAN,
			is_active BOOLEAN,
			created_at TIMESTAMP,
			updated_at TIMESTAMP
		)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			t.Fatalf("create settings schema: %v", err)
		}
	}
}

// seedUser inserts an administrator row with the given stored credential. An empty
// stored value is inserted as NULL (the broken/legacy state).
func seedUser(t *testing.T, path, username, stored string) {
	t.Helper()
	db := openStore(t, path)
	var v any
	if stored != "" {
		v = stored
	}
	if _, err := db.Exec(`INSERT INTO users (username, password_hash, email, full_name, is_admin, is_active, created_at, updated_at)
		VALUES (?, ?, '', '', true, true, current_timestamp, current_timestamp)`, username, v); err != nil {
		t.Fatalf("seed user: %v", err)
	}
}

// storedCredential returns the stored password credential for a user, or "" when the
// user (or the database) does not exist.
func storedCredential(t *testing.T, path, username string) string {
	t.Helper()
	if _, err := os.Stat(path); err != nil {
		return ""
	}
	db := openStore(t, path)
	var h sql.NullString
	err := db.QueryRow(`SELECT password_hash FROM users WHERE lower(trim(username)) = lower(trim(?))`, username).Scan(&h)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(h.String)
}
