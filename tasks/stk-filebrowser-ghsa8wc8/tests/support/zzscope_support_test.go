package fbhttp

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/asdine/storm/v3"
	"github.com/golang-jwt/jwt/v5"

	"github.com/filebrowser/filebrowser/v2/settings"
	"github.com/filebrowser/filebrowser/v2/storage"
	"github.com/filebrowser/filebrowser/v2/storage/bolt"
	"github.com/filebrowser/filebrowser/v2/users"
)

// zzScopeEnv is a real storage (bolt) whose single user is scoped to a
// per-test directory, plus an "outside" directory that belongs to no user.
// The filesystem is built by the product's own user loading path, so the
// scoping works the same way it does in production.
type zzScopeEnv struct {
	t       *testing.T
	st      *storage.Storage
	root    string
	scope   string
	outside string
	key     []byte
	token   string
}

func zzNewEnv(t *testing.T, perm users.Permissions) *zzScopeEnv {
	t.Helper()
	base := t.TempDir()
	root := filepath.Join(base, "root")
	scope := filepath.Join(root, "user")
	outside := filepath.Join(base, "outside")
	for _, dir := range []string{scope, outside} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			t.Fatal(err)
		}
	}

	db, err := storm.Open(filepath.Join(t.TempDir(), "db"))
	if err != nil {
		t.Fatalf("open storage: %v", err)
	}
	t.Cleanup(func() { _ = db.Close() })

	st, err := bolt.NewStorage(db)
	if err != nil {
		t.Fatalf("storage: %v", err)
	}
	if err := st.Users.Save(&users.User{
		Username: "scoped",
		Password: "pw",
		Scope:    "/user",
		Perm:     perm,
	}); err != nil {
		t.Fatalf("save user: %v", err)
	}

	key := []byte("zz-scope-signing-key")
	if err := st.Settings.Save(&settings.Settings{Key: key}); err != nil {
		t.Fatalf("save settings: %v", err)
	}

	claims := &authToken{
		User: userInfo{ID: 1, Username: "scoped", Perm: perm},
		RegisteredClaims: jwt.RegisteredClaims{
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-time.Minute)),
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
		},
	}
	signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(key)
	if err != nil {
		t.Fatalf("sign token: %v", err)
	}

	return &zzScopeEnv{t: t, st: st, root: root, scope: scope, outside: outside, key: key, token: signed}
}

func (e *zzScopeEnv) req(h handleFunc, method, target, body string, headers map[string]string) *httptest.ResponseRecorder {
	e.t.Helper()
	r, err := http.NewRequest(method, target, bytes.NewReader([]byte(body)))
	if err != nil {
		e.t.Fatalf("new request: %v", err)
	}
	r.Header.Set("X-Auth", e.token)
	for k, v := range headers {
		r.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	handle(h, "", e.st, &settings.Server{Root: e.root}).ServeHTTP(rec, r)
	return rec
}

func (e *zzScopeEnv) link(oldname, newname string) {
	e.t.Helper()
	if err := os.Symlink(oldname, newname); err != nil {
		e.t.Skipf("cannot create symlink: %v", err)
	}
}

func (e *zzScopeEnv) write(rel, content string) {
	e.t.Helper()
	p := filepath.Join(e.scope, rel)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		e.t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		e.t.Fatal(err)
	}
}

func (e *zzScopeEnv) mkdir(rel string) {
	e.t.Helper()
	if err := os.MkdirAll(filepath.Join(e.scope, rel), 0o755); err != nil {
		e.t.Fatal(err)
	}
}

func zzRequireClientError(t *testing.T, rec *httptest.ResponseRecorder, what string) {
	t.Helper()
	if rec.Code < 400 || rec.Code > 499 {
		t.Fatalf("%s: expected a client error and no change outside the scope, got status %d (body %q)",
			what, rec.Code, strings.TrimSpace(rec.Body.String()))
	}
}

func zzRequireNoFile(t *testing.T, p, what string) {
	t.Helper()
	if _, err := os.Stat(p); err == nil {
		t.Fatalf("%s: %s exists outside the scope", what, p)
	}
}

func zzRequireFile(t *testing.T, p, want, what string) {
	t.Helper()
	data, err := os.ReadFile(p)
	if err != nil {
		t.Fatalf("%s: %s was not written: %v", what, p, err)
	}
	if string(data) != want {
		t.Fatalf("%s: %s contains %q, want %q", what, p, string(data), want)
	}
}
