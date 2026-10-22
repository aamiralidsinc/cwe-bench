package routes

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/howznguyen/knowns/internal/storage"
)

const zzKnownsRouteMarker = "ZZ-KNOWNS-ROUTE-SECRET-9ab2"

func zzKnownsRouteStore(t *testing.T) (*storage.Store, string) {
	t.Helper()
	t.Setenv("HOME", t.TempDir())
	base := t.TempDir()
	store := storage.NewStore(filepath.Join(base, ".knowns"))
	if err := store.Init("zz-knows-route-sec"); err != nil {
		t.Fatalf("init store: %v", err)
	}
	return store, base
}

func zzKnownsRouteWrite(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir for %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func zzKnownsRouteDo(t *testing.T, router http.Handler, method, target string, body any) *httptest.ResponseRecorder {
	t.Helper()
	var reader *bytes.Reader
	if body == nil {
		reader = bytes.NewReader(nil)
	} else {
		data, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("marshal body: %v", err)
		}
		reader = bytes.NewReader(data)
	}
	req := httptest.NewRequest(method, target, reader)
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	return w
}

func zzKnownsRouteRefused(t *testing.T, w *httptest.ResponseRecorder) {
	t.Helper()
	if w.Code < 400 || w.Code > 499 {
		t.Fatalf("status %d, want a client error; body: %s", w.Code, w.Body.String())
	}
}

func zzKnownsRouteNoLeak(t *testing.T, w *httptest.ResponseRecorder) {
	t.Helper()
	if strings.Contains(w.Body.String(), zzKnownsRouteMarker) {
		t.Fatalf("response carried the outside file's contents: %s", w.Body.String())
	}
}

func zzKnownsRouteDoc(marker string) string {
	return "---\ntitle: Outside file\n---\n\n" + marker + "\n"
}

func zzKnownsRouteMemory(id, layer, body string) string {
	return "---\nid: " + id + "\ntitle: Legit entry\nlayer: " + layer + "\ncategory: pattern\nstatus: active\nconfidence: medium\nttlDays: 30\nsources: []\ntags: []\ncreatedAt: '2026-01-01T00:00:00.000Z'\nupdatedAt: '2026-01-01T00:00:00.000Z'\n---\n\n" + body + "\n"
}

// A document requested through the web API by a name that walks up must not be
// served, in any spelling (plain or URL-encoded).
func TestSecZZDocRouteReadTraversal(t *testing.T) {
	store, base := zzKnownsRouteStore(t)
	zzKnownsRouteWrite(t, filepath.Join(base, ".knowns", "secret.md"), zzKnownsRouteDoc(zzKnownsRouteMarker))
	router := chi.NewRouter()
	(&DocRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	for _, target := range []string{
		"/docs/../secret",
		"/docs/%2e%2e%2fsecret",
		"/docs/..%2fsecret",
	} {
		w := zzKnownsRouteDo(t, router, http.MethodGet, target, nil)
		zzKnownsRouteRefused(t, w)
		zzKnownsRouteNoLeak(t, w)
	}
}

// The preview's template-file selector is caller-supplied and must not read a
// file outside the template library.
func TestSecZZPreviewFileTraversal(t *testing.T) {
	store, base := zzKnownsRouteStore(t)
	router := chi.NewRouter()
	(&TemplateRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	w := zzKnownsRouteDo(t, router, http.MethodPost, "/templates", map[string]any{"name": "zz-preview-t", "description": "d"})
	if w.Code != http.StatusCreated {
		t.Fatalf("setup template create status %d: %s", w.Code, w.Body.String())
	}
	zzKnownsRouteWrite(t, filepath.Join(base, "zz-outside.txt"), zzKnownsRouteMarker)

	w = zzKnownsRouteDo(t, router, http.MethodPost, "/templates/preview", map[string]any{
		"name":         "zz-preview-t",
		"templateFile": "../../../zz-outside.txt",
	})
	zzKnownsRouteRefused(t, w)
	zzKnownsRouteNoLeak(t, w)
}

// The preview also reports the destination file's current contents; the
// destination comes from template actions after request-variable substitution,
// so it must not read a file outside the project.
func TestSecZZPreviewDestinationTraversal(t *testing.T) {
	store, base := zzKnownsRouteStore(t)
	dir := filepath.Join(base, ".knowns", "templates", "zz-dest")
	zzKnownsRouteWrite(t, filepath.Join(dir, "_template.yaml"),
		"name: zz-dest\ndestination: \"\"\nactions:\n  - type: add\n    template: main.hbs\n    path: \"{{file}}\"\n")
	zzKnownsRouteWrite(t, filepath.Join(dir, "main.hbs"), "rendered body")
	zzKnownsRouteWrite(t, filepath.Join(filepath.Dir(base), "zz-outside.txt"), zzKnownsRouteMarker)

	router := chi.NewRouter()
	(&TemplateRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)
	w := zzKnownsRouteDo(t, router, http.MethodPost, "/templates/preview", map[string]any{
		"name":         "zz-dest",
		"templateFile": "main.hbs",
		"variables":    map[string]string{"file": "../zz-outside.txt"},
	})
	zzKnownsRouteRefused(t, w)
	zzKnownsRouteNoLeak(t, w)
}

// The raw-source view of a document must not serve a file outside the document
// library.
func TestSecZZDocSourceTraversal(t *testing.T) {
	store, base := zzKnownsRouteStore(t)
	zzKnownsRouteWrite(t, filepath.Join(base, "secret.md"), zzKnownsRouteDoc(zzKnownsRouteMarker))
	router := chi.NewRouter()
	(&DocRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	w := zzKnownsRouteDo(t, router, http.MethodGet, "/docs/x/../../../secret/source", nil)
	zzKnownsRouteRefused(t, w)
	zzKnownsRouteNoLeak(t, w)
}

// The identifier a memory record stores in its own metadata is untrusted when
// the record is promoted through the web API.
func TestSecZZMemoryPromoteStoredIdentifierRoute(t *testing.T) {
	store, base := zzKnownsRouteStore(t)
	home := os.Getenv("HOME")
	original := filepath.Join(base, ".knowns", "memory", "memory-legit.md")
	zzKnownsRouteWrite(t, original, zzKnownsRouteMemory("x/../../../zz-escaped-promote-route", "project", "legit body"))

	router := chi.NewRouter()
	(&MemoryRoutes{store: store}).Register(router)
	w := zzKnownsRouteDo(t, router, http.MethodPost, "/memories/legit/promote", nil)
	zzKnownsRouteRefused(t, w)

	for _, path := range []string{
		filepath.Join(home, "zz-escaped-promote-route.md"),
		filepath.Join(base, "zz-escaped-promote-route.md"),
	} {
		if _, err := os.Stat(path); !os.IsNotExist(err) {
			t.Fatalf("%s exists; the promote wrote outside the memory roots (stat err: %v)", path, err)
		}
	}
	if _, err := os.Stat(original); err != nil {
		t.Fatalf("the stored record was moved by a refused promote: %v", err)
	}
}
