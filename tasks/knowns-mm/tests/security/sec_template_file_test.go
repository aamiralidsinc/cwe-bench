package routes

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/howznguyen/knowns/internal/storage"
)

const secSecret = "SECRET-MARKER-DO-NOT-LEAK"

// A file name chosen by the caller selects a file inside a template's own
// directory when the web interface previews it. Parent segments must not carry
// that read outside the template.

func TestSec_TemplatePreviewFileEscapes(t *testing.T) {
	base := t.TempDir()
	root := filepath.Join(base, ".knowns")
	t.Setenv("HOME", filepath.Join(base, "home"))
	store := storage.NewStore(root)
	if err := store.Init("sec-preview"); err != nil {
		t.Fatalf("store.Init: %v", err)
	}
	if err := store.Templates.Create("demo", "demo template"); err != nil {
		t.Fatalf("Templates.Create: %v", err)
	}

	victim := filepath.Join(base, "victim.hbs")
	if err := os.WriteFile(victim, []byte(secSecret), 0o644); err != nil {
		t.Fatal(err)
	}

	router := chi.NewRouter()
	(&TemplateRoutes{store: store}).Register(router)

	body, _ := json.Marshal(map[string]any{
		"name":         "demo",
		"templateFile": "../../../victim.hbs",
		"variables":    map[string]any{},
	})
	req := httptest.NewRequest("POST", "/templates/preview", bytes.NewReader(body))
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// Refusal is a client error. A success that discloses the file, or a crash,
	// is not a refusal.
	if w.Code < 400 || w.Code >= 500 {
		t.Fatalf("hostile template file was not refused as a client error: status=%d body=%s", w.Code, w.Body.String())
	}
	if strings.Contains(w.Body.String(), secSecret) {
		t.Fatalf("content outside the template directory was disclosed")
	}
}
