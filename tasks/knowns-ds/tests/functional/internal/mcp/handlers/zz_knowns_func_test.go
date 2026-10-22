package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/howznguyen/knowns/internal/models"
	"github.com/howznguyen/knowns/internal/storage"
	"github.com/mark3labs/mcp-go/mcp"
)

func zzFuncStore(t *testing.T) (*storage.Store, string) {
	t.Helper()
	t.Setenv("HOME", t.TempDir())
	base := t.TempDir()
	store := storage.NewStore(filepath.Join(base, ".knowns"))
	if err := store.Init("zz-knows-func"); err != nil {
		t.Fatalf("init store: %v", err)
	}
	return store, base
}

func zzFuncCall(t *testing.T, handler zzKnownsHandler, store *storage.Store, args map[string]any) *mcp.CallToolResult {
	t.Helper()
	res, err := handler(func() *storage.Store { return store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
	if err != nil {
		t.Fatalf("handler error: %v", err)
	}
	if res == nil {
		t.Fatal("nil tool result")
	}
	return res
}

func zzFuncText(res *mcp.CallToolResult) string {
	var b strings.Builder
	for _, c := range res.Content {
		if text, ok := c.(mcp.TextContent); ok {
			b.WriteString(text.Text)
		}
	}
	return b.String()
}

func zzFuncMustSucceed(t *testing.T, res *mcp.CallToolResult) string {
	t.Helper()
	if res.IsError {
		t.Fatalf("legitimate operation refused: %s", zzFuncText(res))
	}
	return zzFuncText(res)
}

func zzFuncWrite(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir for %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

// Ordinary document use: folders, the .md suffix, and file names that contain
// dots must keep working, including update, rename and delete.
func TestFuncZZDocNestedLifecycle(t *testing.T) {
	store, _ := zzFuncStore(t)

	res := zzFuncCall(t, handleDocCreate, store, map[string]any{
		"title":   "Setup Guide",
		"folder":  "guides",
		"content": "first body",
	})
	zzFuncMustSucceed(t, res)

	for _, path := range []string{"guides/setup-guide", "guides/setup-guide.md"} {
		res = zzFuncCall(t, handleDocGet, store, map[string]any{"path": path})
		text := zzFuncMustSucceed(t, res)
		if !strings.Contains(text, "first body") {
			t.Fatalf("get %q did not return the body: %s", path, text)
		}
	}

	// A folder segment that contains two dots is a normal name, not traversal.
	res = zzFuncCall(t, handleDocCreate, store, map[string]any{
		"title":   "Notes",
		"folder":  "guides/v1..2",
		"content": "dotted folder body",
	})
	zzFuncMustSucceed(t, res)
	res = zzFuncCall(t, handleDocGet, store, map[string]any{"path": "guides/v1..2/notes"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "dotted folder body") {
		t.Fatalf("dotted folder doc not readable: %s", text)
	}

	res = zzFuncCall(t, handleDocUpdate, store, map[string]any{
		"path":    "guides/setup-guide",
		"content": "second body",
	})
	zzFuncMustSucceed(t, res)

	res = zzFuncCall(t, handleDocUpdate, store, map[string]any{
		"path":    "guides/setup-guide",
		"newPath": "guides/advanced/setup-guide",
	})
	zzFuncMustSucceed(t, res)

	res = zzFuncCall(t, handleDocGet, store, map[string]any{"path": "guides/advanced/setup-guide"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "second body") {
		t.Fatalf("renamed doc did not keep its content: %s", text)
	}
	res = zzFuncCall(t, handleDocGet, store, map[string]any{"path": "guides/setup-guide"})
	if !res.IsError {
		t.Fatalf("old path is still readable after a rename: %s", zzFuncText(res))
	}

	res = zzFuncCall(t, handleDocDelete, store, map[string]any{"path": "guides/advanced/setup-guide", "dryRun": false})
	zzFuncMustSucceed(t, res)
	res = zzFuncCall(t, handleDocGet, store, map[string]any{"path": "guides/advanced/setup-guide"})
	if !res.IsError {
		t.Fatalf("deleted doc is still readable: %s", zzFuncText(res))
	}
}

// Imported documents are resolved both by their full path and by the short
// reference that omits the import source name.
func TestFuncZZDocImportedShortReference(t *testing.T) {
	store, base := zzFuncStore(t)
	zzFuncWrite(t, filepath.Join(base, ".knowns", "imports", "src", "docs", "src", "patterns", "foo.md"),
		"---\ntitle: Imported Foo\n---\n\nimported pattern body\n")

	for _, path := range []string{"patterns/foo", "src/patterns/foo"} {
		res := zzFuncCall(t, handleDocGet, store, map[string]any{"path": path})
		text := zzFuncMustSucceed(t, res)
		if !strings.Contains(text, "imported pattern body") {
			t.Fatalf("get %q did not return the imported doc: %s", path, text)
		}
	}
}

// Ordinary memory use: a dotted identifier, update, promote/demote between the
// project and machine layers, and delete.
func TestFuncZZMemoryLifecycleWithDottedID(t *testing.T) {
	store, _ := zzFuncStore(t)

	res := zzFuncCall(t, handleMemoryResolve, store, map[string]any{
		"resolution": "create_proposed",
		"id":         "note.v1",
		"title":      "Dotted note",
		"content":    "first memory body",
	})
	zzFuncMustSucceed(t, res)

	res = zzFuncCall(t, handleMemoryGet, store, map[string]any{"id": "note.v1"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "first memory body") {
		t.Fatalf("get did not return the memory: %s", text)
	}

	res = zzFuncCall(t, handleMemoryUpdate, store, map[string]any{"id": "note.v1", "content": "second memory body"})
	zzFuncMustSucceed(t, res)
	res = zzFuncCall(t, handleMemoryGet, store, map[string]any{"id": "note.v1"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "second memory body") {
		t.Fatalf("updated memory body missing: %s", text)
	}

	res = zzFuncCall(t, handleMemoryPromote, store, map[string]any{"id": "note.v1"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, `"layer": "global"`) {
		t.Fatalf("promote did not move the memory to the global layer: %s", text)
	}
	res = zzFuncCall(t, handleMemoryGet, store, map[string]any{"id": "note.v1"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, `"layer": "global"`) {
		t.Fatalf("promoted memory is not readable from the global layer: %s", text)
	}

	res = zzFuncCall(t, handleMemoryDemote, store, map[string]any{"id": "note.v1"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, `"layer": "project"`) {
		t.Fatalf("demote did not move the memory back to the project layer: %s", text)
	}

	res = zzFuncCall(t, handleMemoryDelete, store, map[string]any{"id": "note.v1", "dryRun": false})
	zzFuncMustSucceed(t, res)
	res = zzFuncCall(t, handleMemoryGet, store, map[string]any{"id": "note.v1"})
	if !res.IsError {
		t.Fatalf("deleted memory is still readable: %s", zzFuncText(res))
	}
}

// A reference written as a title slug (not the stored identifier) still
// resolves to the memory whose title it slugifies.
func TestFuncZZMemoryTitleSlugReference(t *testing.T) {
	store, _ := zzFuncStore(t)
	res := zzFuncCall(t, handleMemoryAdd, store, map[string]any{
		"title":    "Security Pattern",
		"category": "pattern",
		"content":  "Prefer explicit allow lists.",
	})
	zzFuncMustSucceed(t, res)

	entry, err := store.Memory.ResolveReferenceTarget("security-pattern")
	if err != nil {
		t.Fatalf("title-slug reference did not resolve: %v", err)
	}
	if entry.Title != "Security Pattern" {
		t.Fatalf("resolved entry title = %q, want Security Pattern", entry.Title)
	}
}

// The snapshot view returns the copy taken before the last update.
func TestFuncZZMemorySnapshotContent(t *testing.T) {
	store, _ := zzFuncStore(t)
	entry := &models.MemoryEntry{
		ID:       "legit",
		Title:    "Setup note",
		Layer:    models.MemoryLayerProject,
		Category: "pattern",
		Content:  "old body",
	}
	if err := store.Memory.Create(entry); err != nil {
		t.Fatalf("create memory: %v", err)
	}

	res := zzFuncCall(t, handleMemoryUpdate, store, map[string]any{"id": "legit", "content": "new body"})
	zzFuncMustSucceed(t, res)

	res = zzFuncCall(t, handleMemoryGet, store, map[string]any{"id": "legit"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "new body") {
		t.Fatalf("current memory content missing: %s", text)
	}
	res = zzFuncCall(t, handleMemorySnapshot, store, map[string]any{"id": "legit", "layer": "project"})
	text := zzFuncMustSucceed(t, res)
	if !strings.Contains(text, "old body") || strings.Contains(text, "new body") {
		t.Fatalf("snapshot did not return the pre-update copy: %s", text)
	}
}

// Local template names may contain dots; import-qualified names contain a slash
// by design and must keep resolving.
func TestFuncZZTemplateLocalAndImported(t *testing.T) {
	store, base := zzFuncStore(t)

	res := zzFuncCall(t, handleTemplateCreate, store, map[string]any{"name": "my.template", "description": "local"})
	zzFuncMustSucceed(t, res)
	res = zzFuncCall(t, handleTemplateGet, store, map[string]any{"name": "my.template"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "my.template") {
		t.Fatalf("local dotted template name did not resolve: %s", text)
	}
	res = zzFuncCall(t, handleTemplateRun, store, map[string]any{"name": "my.template", "dryRun": true})
	zzFuncMustSucceed(t, res)

	zzFuncWrite(t, filepath.Join(base, ".knowns", "imports", "imp", "templates", "tmpl", "_template.yaml"),
		"name: imported-tmpl\ndescription: imported\nactions:\n  - type: add\n    template: main.hbs\n    path: \"out.ts\"\n")
	zzFuncWrite(t, filepath.Join(base, ".knowns", "imports", "imp", "templates", "tmpl", "main.hbs"), "body")
	res = zzFuncCall(t, handleTemplateGet, store, map[string]any{"name": "imp/tmpl"})
	if text := zzFuncMustSucceed(t, res); !strings.Contains(text, "imported-tmpl") {
		t.Fatalf("import-qualified template name did not resolve: %s", text)
	}
}
