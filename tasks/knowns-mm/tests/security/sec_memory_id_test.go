package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A memory identifier chosen by the caller becomes part of the file location
// under the memory directory. Parent segments must not carry the lookup outside
// that directory.

func TestSec_MemoryGetIDEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	// the stored filename wraps the identifier, so one extra parent segment is
	// needed to leave the memory directory
	res, err := secMemoryGet(e, map[string]any{"id": "../../../../victim"})
	if !secRefused(res, err) {
		t.Fatalf("hostile identifier was not refused: body=%s", secBody(res))
	}
	if strings.Contains(secBody(res), secSecret) {
		t.Fatalf("content outside the memory directory was disclosed")
	}
}

func TestSec_MemoryDeleteIDEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	before := e.readVictim()
	res, err := secMemoryDelete(e, map[string]any{"id": "../../../../victim", "dryRun": false})
	if !secRefused(res, err) {
		t.Fatalf("hostile identifier was not refused: body=%s", secBody(res))
	}
	if !e.victimExists() {
		t.Fatalf("file outside the memory directory was removed")
	}
	if e.readVictim() != before {
		t.Fatalf("file outside the memory directory was changed")
	}
}

// An identifier already recorded in a stored record's own metadata is reused
// when that record moves between layers. The move must not leave the layer
// directory.

func TestSec_MemoryStoredIDPromoteEscapes(t *testing.T) {
	e := secSetup(t)
	marker := "escaped-outside"

	memDir := filepath.Join(e.root, "memory")
	if err := os.MkdirAll(memDir, 0o755); err != nil {
		t.Fatal(err)
	}
	// The on-disk filename is ordinary; only the identifier recorded inside is not.
	body := "---\n" +
		"id: ../../../" + marker + "\n" +
		"title: planted\n" +
		"category: note\n" +
		"status: active\n" +
		"confidence: high\n" +
		"lastVerified: '2026-01-01T00:00:00Z'\n" +
		"ttlDays: 365\n" +
		"sources: []\n" +
		"tags: []\n" +
		"createdAt: '2026-01-01T00:00:00Z'\n" +
		"updatedAt: '2026-01-01T00:00:00Z'\n" +
		"layer: project\n" +
		"---\n" +
		"planted body\n"
	if err := os.WriteFile(filepath.Join(memDir, "memory-planted.md"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}

	res, err := secMemoryPromote(e, map[string]any{"id": "planted"})
	if !secRefused(res, err) {
		t.Fatalf("move with a hostile stored identifier was not refused: body=%s", secBody(res))
	}
	found := findNamed(e.base, marker+".md")
	if found != "" {
		t.Fatalf("move wrote outside the memory directory: %s", found)
	}
}

func findNamed(root, name string) string {
	var found string
	_ = filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		if info.Name() == name {
			found = p
		}
		return nil
	})
	return found
}
