package handlers

import (
	"testing"
)

// A document path chosen by the caller is also used to place a copy in the
// archive area. Parent segments must not carry that move outside the project.

func TestSec_DocArchivePathEscapes(t *testing.T) {
	e := secSetup(t)
	e.plantVictim()
	before := e.readVictim()
	res, err := secDocArchive(e, map[string]any{"path": "../../victim"})
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
