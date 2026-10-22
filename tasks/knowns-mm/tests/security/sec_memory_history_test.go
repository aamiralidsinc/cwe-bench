package handlers

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A memory identifier is also used to name a side record in the versions area.
// Parent segments must not carry that read or write outside the project.

func TestSec_MemoryCheckpointIDEscapes(t *testing.T) {
	e := secSetup(t)
	marker := "hist-outside.json"
	res, err := secMemoryCheckpoint(e, map[string]any{"id": "../../../../hist-outside", "title": "x"})
	if !secRefused(res, err) {
		t.Fatalf("hostile identifier was not refused: body=%s", secBody(res))
	}
	found := findNamed(e.base, marker)
	if found != "" {
		t.Fatalf("side record written outside the versions directory: %s", found)
	}
}

func TestSec_MemoryHistoryIDEscapes(t *testing.T) {
	e := secSetup(t)
	// a side record outside that would be read as the entry's history
	victim := filepath.Join(e.base, "leaked-history.json")
	payload := `{"memoryId":"` + secSecret + `","currentVersion":0,"versions":[]}`
	if err := os.WriteFile(victim, []byte(payload), 0o644); err != nil {
		t.Fatal(err)
	}
	res, err := secMemoryHistory(e, map[string]any{"id": "../../../../leaked-history"})
	if !secRefused(res, err) {
		t.Fatalf("hostile identifier was not refused: body=%s", secBody(res))
	}
	if strings.Contains(secBody(res), secSecret) {
		t.Fatalf("content outside the versions directory was disclosed")
	}
}
