package unarchive_test

import (
	"os"
	"path/filepath"
	"testing"
)

func TestSec_EntryDotDot(t *testing.T) {
	_, dest, outside := fixtureWithOutside(t)
	data := buildTarGz(t, []archiveEntry{{name: "../outside/target", body: []byte(overwrite)}})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive entry escaping the install directory must be refused")
	}
	requireSentinelIntact(t, outside)
}

func TestSec_EntryBackslash(t *testing.T) {
	_, dest, outside := fixtureWithOutside(t)
	data := buildTarGz(t, []archiveEntry{{name: `..\outside\target`, body: []byte(overwrite)}})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive entry escaping the install directory must be refused")
	}
	requireSentinelIntact(t, outside)
}

func TestSec_EntrySiblingPrefix(t *testing.T) {
	parent, dest, _ := fixtureDirs(t)
	sibling := filepath.Join(parent, "dest-sibling", "evil")
	data := buildTarGz(t, []archiveEntry{{name: "../dest-sibling/evil", body: []byte(overwrite)}})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive entry escaping the install directory must be refused")
	}
	if b, err := os.ReadFile(sibling); err == nil {
		t.Fatalf("a file was written outside the install directory: %q", b)
	}
}

func TestSec_EntryCreatesNoOutsideDirectory(t *testing.T) {
	parent, dest, _ := fixtureDirs(t)
	outsideDir := filepath.Join(parent, "newdir")
	data := buildTarGz(t, []archiveEntry{{name: "../newdir/evil", body: []byte(overwrite)}})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive entry escaping the install directory must be refused")
	}
	if _, err := os.Stat(outsideDir); err == nil {
		t.Fatal("a directory outside the install directory was created")
	}
}
