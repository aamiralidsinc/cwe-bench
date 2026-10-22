package routes

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/howznguyen/knowns/internal/storage"
)

// The web interface previews a template's default file when the caller names
// none. That must keep working after the fix.

func TestFunc_TemplatePreviewDefaultFile(t *testing.T) {
	base := t.TempDir()
	root := filepath.Join(base, ".knowns")
	t.Setenv("HOME", filepath.Join(base, "home"))
	store := storage.NewStore(root)
	if err := store.Init("func-preview"); err != nil {
		t.Fatalf("store.Init: %v", err)
	}
	if err := store.Templates.Create("demo", "demo template"); err != nil {
		t.Fatalf("Templates.Create: %v", err)
	}
	// the starter file the create scaffolds
	dir := filepath.Join(root, "templates", "demo")

	router := chi.NewRouter()
	(&TemplateRoutes{store: store}).Register(router)

	body, _ := json.Marshal(map[string]any{
		"name":      "demo",
		"variables": map[string]any{"name": "label"},
	})
	req := httptest.NewRequest("POST", "/templates/preview", bytes.NewReader(body))
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("default-file preview failed: status=%d body=%s", w.Code, w.Body.String())
	}

	// and an explicitly named file inside the template still works
	_ = dir
	body, _ = json.Marshal(map[string]any{
		"name":         "demo",
		"templateFile": "main.hbs",
		"variables":    map[string]any{"name": "label"},
	})
	req = httptest.NewRequest("POST", "/templates/preview", bytes.NewReader(body))
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("named-file preview failed: status=%d body=%s", w.Code, w.Body.String())
	}
}
