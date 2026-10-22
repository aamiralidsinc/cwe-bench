package routes

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/howznguyen/knowns/internal/models"
	"github.com/howznguyen/knowns/internal/storage"
)

func zzFuncRouteStore(t *testing.T) (*storage.Store, string) {
	t.Helper()
	t.Setenv("HOME", t.TempDir())
	base := t.TempDir()
	store := storage.NewStore(filepath.Join(base, ".knowns"))
	if err := store.Init("zz-knows-route-func"); err != nil {
		t.Fatalf("init store: %v", err)
	}
	return store, base
}

// Ordinary document use through the web API: nested reads (with or without the
// .md suffix), updates, renames, history and the raw-source view.
func TestFuncZZDocRouteReadUpdateSource(t *testing.T) {
	store, _ := zzFuncRouteStore(t)
	doc := &models.Doc{Path: "guides/setup", Title: "Setup", Content: "zebra body"}
	if err := store.Docs.Create(doc); err != nil {
		t.Fatalf("create doc: %v", err)
	}
	router := chi.NewRouter()
	(&DocRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	for _, target := range []string{"/docs/guides/setup", "/docs/guides/setup.md"} {
		w := zzKnownsRouteDo(t, router, http.MethodGet, target, nil)
		if w.Code != http.StatusOK || !strings.Contains(w.Body.String(), "zebra body") {
			t.Fatalf("GET %s status %d body %s", target, w.Code, w.Body.String())
		}
	}

	w := zzKnownsRouteDo(t, router, http.MethodPut, "/docs/guides/setup", map[string]any{"content": "updated zebra"})
	if w.Code != http.StatusOK {
		t.Fatalf("update status %d body %s", w.Code, w.Body.String())
	}
	w = zzKnownsRouteDo(t, router, http.MethodGet, "/docs/guides/setup", nil)
	if !strings.Contains(w.Body.String(), "updated zebra") {
		t.Fatalf("updated content missing: %s", w.Body.String())
	}

	w = zzKnownsRouteDo(t, router, http.MethodGet, "/docs/guides/setup/history", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("history status %d body %s", w.Code, w.Body.String())
	}

	w = zzKnownsRouteDo(t, router, http.MethodGet, "/docs/guides/setup/source", nil)
	if w.Code != http.StatusOK {
		t.Fatalf("source status %d body %s", w.Code, w.Body.String())
	}
	if !strings.Contains(w.Body.String(), "updated zebra") || !strings.Contains(w.Body.String(), "title:") {
		t.Fatalf("raw source did not return the stored markdown: %s", w.Body.String())
	}
}

// A rename through the web API keeps working, including a destination folder
// segment that contains dots.
func TestFuncZZDocRouteRenameDottedFolder(t *testing.T) {
	store, _ := zzFuncRouteStore(t)
	if err := store.Docs.Create(&models.Doc{Path: "guides/setup", Title: "Setup", Content: "move me"}); err != nil {
		t.Fatalf("create doc: %v", err)
	}
	router := chi.NewRouter()
	(&DocRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	w := zzKnownsRouteDo(t, router, http.MethodPut, "/docs/guides/setup", map[string]any{
		"path": "guides/v9..10/setup",
	})
	if w.Code != http.StatusOK {
		t.Fatalf("rename status %d body %s", w.Code, w.Body.String())
	}
	w = zzKnownsRouteDo(t, router, http.MethodGet, "/docs/guides/v9..10/setup", nil)
	if w.Code != http.StatusOK || !strings.Contains(w.Body.String(), "move me") {
		t.Fatalf("renamed doc not readable: status %d body %s", w.Code, w.Body.String())
	}
}

// The preview reports the destination file's current contents and the rendered
// template, for an in-project destination.
func TestFuncZZPreviewDestinationContent(t *testing.T) {
	store, base := zzFuncRouteStore(t)
	dir := filepath.Join(base, ".knowns", "templates", "zz-legit-dest")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatalf("mkdir template: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "_template.yaml"), []byte(
		"name: zz-legit-dest\ndestination: \"\"\nactions:\n  - type: add\n    template: main.hbs\n    path: \"src/generated.ts\"\n"), 0o644); err != nil {
		t.Fatalf("write template: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "main.hbs"), []byte("// generated"), 0o644); err != nil {
		t.Fatalf("write hbs: %v", err)
	}
	if err := os.MkdirAll(filepath.Join(base, "src"), 0o755); err != nil {
		t.Fatalf("mkdir src: %v", err)
	}
	if err := os.WriteFile(filepath.Join(base, "src", "generated.ts"), []byte("OLD-CONTENT"), 0o644); err != nil {
		t.Fatalf("write destination: %v", err)
	}

	router := chi.NewRouter()
	(&TemplateRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)
	w := zzKnownsRouteDo(t, router, http.MethodPost, "/templates/preview", map[string]any{
		"name":         "zz-legit-dest",
		"templateFile": "main.hbs",
	})
	if w.Code != http.StatusOK {
		t.Fatalf("preview status %d body %s", w.Code, w.Body.String())
	}
	var payload struct {
		Files []struct {
			Path            string `json:"path"`
			Content         string `json:"content"`
			ExistingContent string `json:"existingContent"`
		} `json:"files"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &payload); err != nil {
		t.Fatalf("decode preview: %v", err)
	}
	if len(payload.Files) != 1 {
		t.Fatalf("preview files = %#v", payload.Files)
	}
	if payload.Files[0].Path != "src/generated.ts" || payload.Files[0].ExistingContent != "OLD-CONTENT" {
		t.Fatalf("preview file = %#v, want in-project destination with its current contents", payload.Files[0])
	}
}

// Creating and previewing a local template renders its variables as today.
func TestFuncZZPreviewRendersVariables(t *testing.T) {
	store, _ := zzFuncRouteStore(t)
	router := chi.NewRouter()
	(&TemplateRoutes{store: store, sse: &fakeBroadcaster{}}).Register(router)

	w := zzKnownsRouteDo(t, router, http.MethodPost, "/templates", map[string]any{"name": "zz-render", "description": "d"})
	if w.Code != http.StatusCreated {
		t.Fatalf("create status %d body %s", w.Code, w.Body.String())
	}
	w = zzKnownsRouteDo(t, router, http.MethodPost, "/templates/preview", map[string]any{
		"name":      "zz-render",
		"variables": map[string]string{"name": "world"},
	})
	if w.Code != http.StatusOK {
		t.Fatalf("preview status %d body %s", w.Code, w.Body.String())
	}
	if !strings.Contains(w.Body.String(), "Generated: world") || !strings.Contains(w.Body.String(), "world.ts") {
		t.Fatalf("preview did not render variables: %s", w.Body.String())
	}
}

// Promoting and demoting a memory through the web API keeps working.
func TestFuncZZMemoryRoutePromoteDemote(t *testing.T) {
	store, _ := zzFuncRouteStore(t)
	if err := store.Memory.Create(&models.MemoryEntry{
		ID:       "legit",
		Title:    "Route note",
		Layer:    models.MemoryLayerProject,
		Category: "pattern",
		Content:  "route body",
	}); err != nil {
		t.Fatalf("create memory: %v", err)
	}
	router := chi.NewRouter()
	(&MemoryRoutes{store: store}).Register(router)

	w := zzKnownsRouteDo(t, router, http.MethodPost, "/memories/legit/promote", nil)
	if w.Code != http.StatusOK || !strings.Contains(w.Body.String(), `"layer":"global"`) {
		t.Fatalf("promote status %d body %s", w.Code, w.Body.String())
	}
	w = zzKnownsRouteDo(t, router, http.MethodPost, "/memories/legit/demote", nil)
	if w.Code != http.StatusOK || !strings.Contains(w.Body.String(), `"layer":"project"`) {
		t.Fatalf("demote status %d body %s", w.Code, w.Body.String())
	}
}
