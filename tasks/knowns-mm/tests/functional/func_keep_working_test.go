package handlers

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/howznguyen/knowns/internal/models"
)

// These behaviours must keep working after the fix. They are the cases an
// over-broad "reject every parent segment or symlink" change would break.

func TestFunc_NestedDocPath(t *testing.T) {
	e := secSetup(t)
	res, err := secDocCreate(e, map[string]any{
		"title":   "Setup",
		"folder":  "guides",
		"content": "hello",
	})
	if err != nil || secRefused(res, err) {
		t.Fatalf("nested create failed: err=%v body=%s", err, secBody(res))
	}
	got, err := secDocGet(e, map[string]any{"path": "guides/setup"})
	if err != nil || secRefused(got, err) {
		t.Fatalf("nested get failed: err=%v body=%s", err, secBody(got))
	}
}

func TestFunc_TrailingMDSuffix(t *testing.T) {
	e := secSetup(t)
	if _, err := secDocCreate(e, map[string]any{"title": "Readme", "content": "body"}); err != nil {
		t.Fatal(err)
	}
	got, err := secDocGet(e, map[string]any{"path": "readme.md"})
	if err != nil || secRefused(got, err) {
		t.Fatalf("lookup with a trailing .md failed: err=%v body=%s", err, secBody(got))
	}
}

func TestFunc_ImportedDocLookup(t *testing.T) {
	e := secSetup(t)
	imp := filepath.Join(e.root, "imports", "src", "docs", "src")
	if err := os.MkdirAll(imp, 0o755); err != nil {
		t.Fatal(err)
	}
	body := "---\ntitle: Imported\ndescription: d\ncreatedAt: '2026-01-01T00:00:00Z'\nupdatedAt: '2026-01-01T00:00:00Z'\ntags: []\n---\nimported body\n"
	if err := os.WriteFile(filepath.Join(imp, "guide.md"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	got, err := secDocGet(e, map[string]any{"path": "src/guide"})
	if err != nil || secRefused(got, err) {
		t.Fatalf("source-qualified lookup failed: err=%v body=%s", err, secBody(got))
	}
	got, err = secDocGet(e, map[string]any{"path": "guide"})
	if err != nil || secRefused(got, err) {
		t.Fatalf("short-path lookup failed: err=%v body=%s", err, secBody(got))
	}
}

func TestFunc_OrdinaryMemoryIDs(t *testing.T) {
	e := secSetup(t)
	for _, id := range []string{"alpha", "a.b-c_d", "v1.2.3"} {
		if err := e.store.Memory.Create(&models.MemoryEntry{
			ID: id, Title: id, Content: "body", Category: "note",
		}); err != nil {
			t.Fatalf("create memory %q: %v", id, err)
		}
		res, err := secMemoryGet(e, map[string]any{"id": id})
		if err != nil || secRefused(res, err) {
			t.Fatalf("get memory %q failed: err=%v body=%s", id, err, secBody(res))
		}
	}
}

func TestFunc_MemoryPromoteOrdinary(t *testing.T) {
	e := secSetup(t)
	if err := e.store.Memory.Create(&models.MemoryEntry{
		ID: "movable", Title: "movable", Content: "body", Category: "note",
	}); err != nil {
		t.Fatal(err)
	}
	res, err := secMemoryPromote(e, map[string]any{"id": "movable"})
	if err != nil || secRefused(res, err) {
		t.Fatalf("promote of an ordinary memory failed: err=%v body=%s", err, secBody(res))
	}
}

func TestFunc_TemplateImportName(t *testing.T) {
	e := secSetup(t)
	imp := filepath.Join(e.root, "imports", "src", "templates", "feat")
	if err := os.MkdirAll(imp, 0o755); err != nil {
		t.Fatal(err)
	}
	meta := "# Template: feat\nname: feat\ndescription: d\nversion: 1.0.0\n"
	if err := os.WriteFile(filepath.Join(imp, "_template.yaml"), []byte(meta), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := secTemplateGet(e, map[string]any{"name": "src/feat"})
	if err != nil || secRefused(res, err) {
		t.Fatalf("import-qualified template lookup failed: err=%v body=%s", err, secBody(res))
	}
}

func TestFunc_InProjectSymlink(t *testing.T) {
	e := secSetup(t)
	if _, err := secDocCreate(e, map[string]any{"title": "Target", "content": "inner"}); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(e.root, "docs", "alias.md")
	target := filepath.Join(e.root, "docs", "target.md")
	if err := os.Symlink(target, link); err != nil {
		t.Skipf("symlink unavailable: %v", err)
	}
	res, err := secDocGet(e, map[string]any{"path": "alias"})
	if err != nil || secRefused(res, err) {
		t.Fatalf("in-project symlink lookup failed: err=%v body=%s", err, secBody(res))
	}
}
