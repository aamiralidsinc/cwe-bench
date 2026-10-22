package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A template name chosen by the caller becomes the template's directory under
// the templates directory. Parent segments must not carry the create outside
// that directory.

func TestSec_TemplateCreateNameEscapes(t *testing.T) {
	e := secSetup(t)
	res, err := secTemplateCreate(e, map[string]any{"name": "../../pwned", "description": "x"})
	if !secRefused(res, err) {
		t.Fatalf("hostile template name was not refused: body=%s", secBody(res))
	}
	outside := filepath.Join(e.base, "pwned")
	if _, err := os.Stat(outside); err == nil {
		t.Fatalf("template directory created outside the templates directory")
	}
}

func TestSec_TemplateGetNameEscapes(t *testing.T) {
	e := secSetup(t)
	// a file outside that would be read as a template's own metadata
	outsideDir := filepath.Join(e.base, "leaked")
	if err := os.MkdirAll(outsideDir, 0o755); err != nil {
		t.Fatal(err)
	}
	meta := "# Template: leaked\nname: leaked\ndescription: " + secSecret + "\nversion: 1.0.0\n"
	if err := os.WriteFile(filepath.Join(outsideDir, "_template.yaml"), []byte(meta), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := secTemplateGet(e, map[string]any{"name": "../../../leaked"})
	if !secRefused(res, err) {
		t.Fatalf("hostile template name was not refused: body=%s", secBody(res))
	}
	if strings.Contains(secBody(res), secSecret) {
		t.Fatalf("content outside the templates directory was disclosed")
	}
}
