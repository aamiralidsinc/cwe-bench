package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A document folder chosen by the caller becomes part of the file location
// under the documentation directory. Parent segments must not carry the write
// outside that directory.

func TestSec_DocCreateFolderEscapes(t *testing.T) {
	e := secSetup(t)
	res, err := secDocCreate(e, map[string]any{
		"title":  "pwned",
		"folder": "../..",
	})
	if !secRefused(res, err) {
		t.Fatalf("hostile folder was not refused: body=%s", secBody(res))
	}
	outside := filepath.Join(e.base, "pwned.md")
	if _, err := os.Stat(outside); err == nil {
		t.Fatalf("document written outside the documentation directory")
	}
	if e.victimExists() {
		t.Fatalf("victim outside the documentation directory was touched")
	}
}

// The same caller-supplied folder, read back.

func TestSec_DocGetPathEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	res, err := secDocGet(e, map[string]any{"path": "../../victim"})
	if !secRefused(res, err) {
		t.Fatalf("hostile path was not refused: body=%s", secBody(res))
	}
	if strings.Contains(secBody(res), secSecret) {
		t.Fatalf("content outside the documentation directory was disclosed")
	}
}

// And removed.

func TestSec_DocDeletePathEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	before := e.readVictim()
	res, err := secDocDelete(e, map[string]any{"path": "../../victim", "dryRun": false})
	if !secRefused(res, err) {
		t.Fatalf("hostile path was not refused: body=%s", secBody(res))
	}
	if !e.victimExists() {
		t.Fatalf("file outside the documentation directory was removed")
	}
	if e.readVictim() != before {
		t.Fatalf("file outside the documentation directory was changed")
	}
}

// A symbolic link inside the documentation directory that points outside it.

func TestSec_DocSymlinkEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	link := filepath.Join(e.root, "docs", "out")
	if err := os.MkdirAll(filepath.Dir(link), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(e.base, link); err != nil {
		t.Skipf("symlink unavailable: %v", err)
	}
	res, err := secDocGet(e, map[string]any{"path": "out/victim"})
	if !secRefused(res, err) {
		t.Fatalf("symlink escape was not refused: body=%s", secBody(res))
	}
	if strings.Contains(secBody(res), secSecret) {
		t.Fatalf("content outside the documentation directory was disclosed")
	}
}
