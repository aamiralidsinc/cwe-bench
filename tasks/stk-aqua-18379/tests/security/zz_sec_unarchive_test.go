package unarchive_test

import (
	"archive/tar"
	"os"
	"path/filepath"
	"testing"
)

// Each case extracts an archive that tries to reach a path outside the install
// directory, and requires a clean refusal plus an unchanged outside file.

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

func TestSec_SymlinkAbsoluteTarget(t *testing.T) {
	_, dest, outside := fixtureWithOutside(t)
	data := buildTarGz(t, []archiveEntry{
		{name: "sub/link", typ: tar.TypeSymlink, link: outside},
		{name: "sub/link", body: []byte(overwrite)},
	})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive with a link leaving the install directory must be refused")
	}
	requireSentinelIntact(t, outside)
}

func TestSec_SymlinkRelativeTarget(t *testing.T) {
	_, dest, outside := fixtureWithOutside(t)
	data := buildTarGz(t, []archiveEntry{
		{name: "sub/link", typ: tar.TypeSymlink, link: "../../outside/target"},
		{name: "sub/link", body: []byte(overwrite)},
	})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive with a link leaving the install directory must be refused")
	}
	requireSentinelIntact(t, outside)
}

func TestSec_HardlinkNestedTarget(t *testing.T) {
	_, dest, outside := fixtureWithOutside(t)
	data := buildTarGz(t, []archiveEntry{
		{name: "sub/h", typ: tar.TypeLink, link: "../outside/target"},
		{name: "sub/h", body: []byte(overwrite)},
	})
	if err := extractTarGz(data, dest); err == nil {
		t.Fatal("extraction of an archive with a link leaving the install directory must be refused")
	}
	requireSentinelIntact(t, outside)
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
