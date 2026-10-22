package handlers

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/howznguyen/knowns/internal/storage"
	"github.com/mark3labs/mcp-go/mcp"
)

// The marker only exists in files the product must never reach.
const zzKnownsSecMarker = "ZZ-KNOWNS-SECRET-4c1d"

type zzKnownsHandler func(func() *storage.Store, mcp.CallToolRequest) (*mcp.CallToolResult, error)

func zzKnownsStore(t *testing.T) (*storage.Store, string) {
	t.Helper()
	t.Setenv("HOME", t.TempDir())
	base := t.TempDir()
	store := storage.NewStore(filepath.Join(base, ".knowns"))
	if err := store.Init("zz-knows-sec"); err != nil {
		t.Fatalf("init store: %v", err)
	}
	return store, base
}

func zzKnownsWrite(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir for %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func zzKnownsCall(t *testing.T, handler zzKnownsHandler, store *storage.Store, args map[string]any) *mcp.CallToolResult {
	t.Helper()
	res, err := handler(func() *storage.Store { return store }, mcp.CallToolRequest{
		Params: mcp.CallToolParams{Arguments: args},
	})
	if err != nil {
		t.Fatalf("handler returned a transport error instead of a tool result: %v", err)
	}
	return res
}

func zzKnownsResultText(res *mcp.CallToolResult) string {
	if res == nil {
		return ""
	}
	var b strings.Builder
	for _, c := range res.Content {
		if text, ok := c.(mcp.TextContent); ok {
			b.WriteString(text.Text)
		}
	}
	return b.String()
}

func zzKnownsRefused(t *testing.T, res *mcp.CallToolResult) {
	t.Helper()
	if res == nil {
		t.Fatal("nil tool result")
	}
	if !res.IsError {
		t.Fatalf("operation succeeded but must be refused; result: %s", zzKnownsResultText(res))
	}
}

func zzKnownsNoLeak(t *testing.T, res *mcp.CallToolResult) {
	t.Helper()
	if strings.Contains(zzKnownsResultText(res), zzKnownsSecMarker) {
		t.Fatalf("response carried the outside file's contents: %s", zzKnownsResultText(res))
	}
}

func zzKnownsNotExist(t *testing.T, path string) {
	t.Helper()
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("%s exists (or cannot be stat'ed: %v); the operation wrote outside its root", path, err)
	}
}

func zzKnownsDocContent(marker string) string {
	return "---\ntitle: Outside file\n---\n\n" + marker + "\n"
}

func zzKnownsMemoryContent(id, layer, body string) string {
	return fmt.Sprintf("---\nid: %s\ntitle: Legit entry\nlayer: %s\ncategory: pattern\nstatus: active\nconfidence: medium\nttlDays: 30\nsources: []\ntags: []\ncreatedAt: '2026-01-01T00:00:00.000Z'\nupdatedAt: '2026-01-01T00:00:00.000Z'\n---\n\n%s\n", id, layer, body)
}

// A document name that walks up out of the document library must not be read,
// however it reaches the store (with or without the .md suffix, with or
// without an intermediate segment).
func TestSecZZDocReadTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	zzKnownsWrite(t, filepath.Join(base, ".knowns", "secret.md"), zzKnownsDocContent(zzKnownsSecMarker))

	for _, path := range []string{"../secret", "../secret.md", "x/../../secret"} {
		res := zzKnownsCall(t, handleDocGet, store, map[string]any{"path": path})
		zzKnownsRefused(t, res)
		zzKnownsNoLeak(t, res)
	}
}

// Creating a document whose folder walks up must not create files outside the
// document library.
func TestSecZZDocCreateTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	escaped := filepath.Join(base, "zz-escaped-doc")

	res := zzKnownsCall(t, handleDocCreate, store, map[string]any{
		"title":   "Escaped",
		"folder":  "x/../../../zz-escaped-doc",
		"content": zzKnownsSecMarker,
	})
	zzKnownsRefused(t, res)
	zzKnownsNotExist(t, filepath.Join(escaped, "escaped.md"))
}

// Renaming a document to a path that walks up must not write the new file
// outside the library and must leave the original document untouched.
func TestSecZZDocRenameTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	res := zzKnownsCall(t, handleDocCreate, store, map[string]any{"title": "Safe Doc", "content": "original body"})
	if res.IsError {
		t.Fatalf("setup create failed: %s", zzKnownsResultText(res))
	}

	res = zzKnownsCall(t, handleDocUpdate, store, map[string]any{
		"path":    "safe-doc",
		"newPath": "x/../../../zz-escaped-renamed",
		"content": zzKnownsSecMarker,
	})
	zzKnownsRefused(t, res)
	zzKnownsNotExist(t, filepath.Join(base, "zz-escaped-renamed.md"))

	res = zzKnownsCall(t, handleDocGet, store, map[string]any{"path": "safe-doc"})
	if res.IsError {
		t.Fatalf("original document disappeared after a refused rename: %s", zzKnownsResultText(res))
	}
}

// Deleting a document by a path that walks up must not remove a file outside
// the document library.
func TestSecZZDocDeleteTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	secret := filepath.Join(base, ".knowns", "secret.md")
	zzKnownsWrite(t, secret, zzKnownsDocContent(zzKnownsSecMarker))

	res := zzKnownsCall(t, handleDocDelete, store, map[string]any{"path": "../secret", "dryRun": false})
	zzKnownsRefused(t, res)
	if _, err := os.Stat(secret); err != nil {
		t.Fatalf("file outside the document library was removed: %v", err)
	}
}

// The imported-document lookup is a second path into the same read; a
// traversing name must not reach a file that sits outside the imported docs.
func TestSecZZDocImportLookupTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	zzKnownsWrite(t, filepath.Join(base, ".knowns", "imports", "src", "secret.md"), zzKnownsDocContent(zzKnownsSecMarker))

	res := zzKnownsCall(t, handleDocGet, store, map[string]any{"path": "../secret"})
	zzKnownsRefused(t, res)
	zzKnownsNoLeak(t, res)
}

// A symbolic link inside the document library whose target is outside it must
// not be followed.
func TestSecZZDocSymlinkEscape(t *testing.T) {
	store, base := zzKnownsStore(t)
	outside := filepath.Join(base, "outside-doc.md")
	zzKnownsWrite(t, outside, zzKnownsDocContent(zzKnownsSecMarker))
	if err := os.Symlink(outside, filepath.Join(base, ".knowns", "docs", "linked.md")); err != nil {
		t.Fatalf("symlink: %v", err)
	}

	res := zzKnownsCall(t, handleDocGet, store, map[string]any{"path": "linked"})
	zzKnownsRefused(t, res)
	zzKnownsNoLeak(t, res)
}

// A memory identifier that walks up must not read a file outside the memory
// library.
func TestSecZZMemoryReadTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	zzKnownsWrite(t, filepath.Join(base, "secret.md"), zzKnownsMemoryContent("outside", "project", zzKnownsSecMarker))

	for _, id := range []string{"x/../../../secret"} {
		res := zzKnownsCall(t, handleMemoryGet, store, map[string]any{"id": id})
		zzKnownsRefused(t, res)
		zzKnownsNoLeak(t, res)
	}
}

// Creating a memory through the review flow with a traversing identifier must
// not write outside the memory library.
func TestSecZZMemoryCreateTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	res := zzKnownsCall(t, handleMemoryResolve, store, map[string]any{
		"resolution": "create_proposed",
		"id":         "x/../../../zz-escaped-memory",
		"content":    zzKnownsSecMarker,
	})
	zzKnownsRefused(t, res)
	zzKnownsNotExist(t, filepath.Join(base, "zz-escaped-memory.md"))
}

// Deleting a memory by a traversing identifier must not remove a file outside
// the memory library.
func TestSecZZMemoryDeleteTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	secret := filepath.Join(base, "secret.md")
	zzKnownsWrite(t, secret, zzKnownsMemoryContent("outside", "project", zzKnownsSecMarker))

	res := zzKnownsCall(t, handleMemoryDelete, store, map[string]any{"id": "x/../../../secret", "dryRun": false})
	zzKnownsRefused(t, res)
	if _, err := os.Stat(secret); err != nil {
		t.Fatalf("file outside the memory library was removed: %v", err)
	}
}

// Identifiers that use platform path syntax (or that end in a dot, which some
// platforms drop) are not valid memory identifiers and must be refused rather
// than written as files.
func TestSecZZMemoryIdentifierShapes(t *testing.T) {
	store, base := zzKnownsStore(t)
	for name, id := range map[string]string{
		"trailing dot": "zzbad.",
		"backslash":    `zzbad\route`,
		"colon":        "zzbad:stream",
	} {
		t.Run(name, func(t *testing.T) {
			res := zzKnownsCall(t, handleMemoryResolve, store, map[string]any{
				"resolution": "create_proposed",
				"id":         id,
				"content":    zzKnownsSecMarker,
			})
			zzKnownsRefused(t, res)
			entries, err := os.ReadDir(filepath.Join(base, ".knowns", "memory"))
			if err != nil && !os.IsNotExist(err) {
				t.Fatalf("read memory dir: %v", err)
			}
			for _, e := range entries {
				if strings.Contains(e.Name(), "zzbad") {
					t.Fatalf("identifier %q was written as %s", id, e.Name())
				}
			}
		})
	}
}

// The identifier a record carries in its own stored metadata is still
// untrusted: promoting or demoting that record must not write a file outside
// the memory roots because of it.
func TestSecZZMemoryPromoteStoredIdentifier(t *testing.T) {
	store, base := zzKnownsStore(t)
	home := os.Getenv("HOME")
	original := filepath.Join(base, ".knowns", "memory", "memory-legit.md")
	zzKnownsWrite(t, original, zzKnownsMemoryContent("x/../../../zz-escaped-promote", "project", "legit body"))

	res := zzKnownsCall(t, handleMemoryPromote, store, map[string]any{"id": "legit"})
	zzKnownsRefused(t, res)
	zzKnownsNotExist(t, filepath.Join(home, "zz-escaped-promote.md"))
	zzKnownsNotExist(t, filepath.Join(base, "zz-escaped-promote.md"))
	if _, err := os.Stat(original); err != nil {
		t.Fatalf("the stored record was moved by a refused promote: %v", err)
	}
}

// The recovery view of a memory must not read a file outside the memory roots
// either.
func TestSecZZMemorySnapshotTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	zzKnownsWrite(t, filepath.Join(base, "secret.md"), zzKnownsMemoryContent("outside", "project", zzKnownsSecMarker))

	res := zzKnownsCall(t, handleMemorySnapshot, store, map[string]any{"id": "x/../../../../secret", "layer": "project"})
	zzKnownsRefused(t, res)
	zzKnownsNoLeak(t, res)
}

// Creating a template whose name walks up must not create files outside the
// template library.
func TestSecZZTemplateCreateTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	res := zzKnownsCall(t, handleTemplateCreate, store, map[string]any{
		"name":        "x/../../../zz-escaped-template",
		"description": "escaped",
	})
	zzKnownsRefused(t, res)
	zzKnownsNotExist(t, filepath.Join(base, "zz-escaped-template", "_template.yaml"))
}

// An import-qualified template name with a traversing tail must not resolve a
// template outside the imported template library.
func TestSecZZTemplateImportTraversal(t *testing.T) {
	store, base := zzKnownsStore(t)
	zzKnownsWrite(t, filepath.Join(base, ".knowns", "imports", "evil-template", "_template.yaml"),
		"name: ZZ-EVIL-TEMPLATE\ndescription: outside\n")

	res := zzKnownsCall(t, handleTemplateGet, store, map[string]any{"name": "x/../../evil-template"})
	zzKnownsRefused(t, res)
	zzKnownsNoLeak(t, res)
}

// Platform path spellings (absolute, backslash, volume, UNC, device) are not
// valid document names and must be refused rather than written as files.
func TestSecZZDocIdentifierShapes(t *testing.T) {
	store, base := zzKnownsStore(t)
	for name, folder := range map[string]string{
		"absolute":            "/tmp/zz-knowns-abs",
		"backslash traversal": `..\..\zz-knowns-bs`,
		"windows volume":      `C:\zz-knowns-vol`,
		"unc":                 `\\server\share\zz-knowns-unc`,
		"device":              `\\?\C:\zz-knowns-dev`,
	} {
		t.Run(name, func(t *testing.T) {
			res := zzKnownsCall(t, handleDocCreate, store, map[string]any{
				"title":   "Shape",
				"folder":  folder,
				"content": zzKnownsSecMarker,
			})
			zzKnownsRefused(t, res)
		})
	}

	err := filepath.WalkDir(base, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if strings.Contains(d.Name(), "zz-knowns") {
			t.Fatalf("path spelling was written as %s", path)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walk: %v", err)
	}
}
