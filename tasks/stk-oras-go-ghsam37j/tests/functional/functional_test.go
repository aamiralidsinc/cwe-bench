// Package htests_functional keeps the store's ordinary behaviour honest: the values a stricter
// containment rule must not break are exercised through the same public entry points.
package htests_functional

import (
	"archive/tar"
	"bytes"
	"os"
	"path/filepath"
	"testing"

	sup "oras.land/oras-go/v2/htests_support"
)

func readOrFail(t *testing.T, path string) []byte {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	return b
}

// A relative link to a sibling member keeps extracting, and keeps its literal target.
func TestRelativeSymlinkInsideExtracts(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/f.txt", Body: "hello world", Type: tar.TypeReg},
		{Name: title + "/s", Link: "f.txt", Type: tar.TypeSymlink},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Fatalf("Push: %v", err)
	}
	link := filepath.Join(workDir, title, "s")
	got, err := os.Readlink(link)
	if err != nil {
		t.Fatalf("Readlink: %v", err)
	}
	if got != "f.txt" {
		t.Fatalf("link target = %q, want %q", got, "f.txt")
	}
	if b := readOrFail(t, link); string(b) != "hello world" {
		t.Fatalf("content through link = %q", b)
	}
}

// An absolute link whose target lies inside the layer keeps extracting unchanged.
func TestAbsoluteSymlinkInsideExtracts(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	target := filepath.Join(workDir, title, "f.txt")
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/f.txt", Body: "hello world", Type: tar.TypeReg},
		{Name: title + "/s", Link: target, Type: tar.TypeSymlink},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Fatalf("Push: %v", err)
	}
	link := filepath.Join(workDir, title, "s")
	got, err := os.Readlink(link)
	if err != nil {
		t.Fatalf("Readlink: %v", err)
	}
	if got != target {
		t.Fatalf("link target = %q, want %q", got, target)
	}
	if b := readOrFail(t, link); string(b) != "hello world" {
		t.Fatalf("content through link = %q", b)
	}
}

// A relative link that climbs and comes back inside the layer keeps extracting.
func TestRelativeSymlinkClimbAndReturnExtracts(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/sub/", Type: tar.TypeDir},
		{Name: title + "/sub/f.txt", Body: "hello world", Type: tar.TypeReg},
		{Name: title + "/sub/s", Link: "../sub/f.txt", Type: tar.TypeSymlink},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Fatalf("Push: %v", err)
	}
	link := filepath.Join(workDir, title, "sub", "s")
	if got, err := os.Readlink(link); err != nil {
		t.Fatalf("Readlink: %v", err)
	} else if got != "../sub/f.txt" {
		t.Fatalf("link target = %q", got)
	}
	if b := readOrFail(t, link); string(b) != "hello world" {
		t.Fatalf("content through link = %q", b)
	}
}

// Extracting the same archive over the same root a second time keeps working.
func TestReextractOverExistingSymlink(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/f.txt", Body: "hello world", Type: tar.TypeReg},
		{Name: title + "/s", Link: "f.txt", Type: tar.TypeSymlink},
	})
	for i := 0; i < 2; i++ {
		if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
			t.Fatalf("Push %d: %v", i+1, err)
		}
	}
	link := filepath.Join(workDir, title, "s")
	if got, err := os.Readlink(link); err != nil {
		t.Fatalf("Readlink: %v", err)
	} else if got != "f.txt" {
		t.Fatalf("link target = %q", got)
	}
	if b := readOrFail(t, link); string(b) != "hello world" {
		t.Fatalf("content through link = %q", b)
	}
}

// The operator option that allows writes outside the working directory keeps its effect.
func TestAllowPathTraversalOnWriteStillWrites(t *testing.T) {
	parent := t.TempDir()
	workDir := filepath.Join(parent, "store")
	if err := os.MkdirAll(workDir, 0o755); err != nil {
		t.Fatal(err)
	}
	s := sup.StoreAt(t, workDir)
	s.AllowPathTraversalOnWrite = true
	blob := []byte("allowed-elsewhere")
	if err := sup.Push(t, s, "../outside.txt", blob, false); err != nil {
		t.Fatalf("Push: %v", err)
	}
	if b := readOrFail(t, filepath.Join(parent, "outside.txt")); !bytes.Equal(b, blob) {
		t.Fatalf("content = %q, want %q", b, blob)
	}
}

// A working directory reached through a link of its own keeps accepting ordinary writes.
func TestPushUnderSymlinkedRoot(t *testing.T) {
	parent := t.TempDir()
	realRoot := filepath.Join(parent, "real")
	if err := os.MkdirAll(realRoot, 0o755); err != nil {
		t.Fatal(err)
	}
	linkRoot := filepath.Join(parent, "link")
	if err := os.Symlink(realRoot, linkRoot); err != nil {
		t.Fatal(err)
	}
	blob := []byte("ordinary-content")
	if err := sup.Push(t, sup.StoreAt(t, linkRoot), "sub/file.txt", blob, false); err != nil {
		t.Fatalf("Push: %v", err)
	}
	if b := readOrFail(t, filepath.Join(realRoot, "sub", "file.txt")); !bytes.Equal(b, blob) {
		t.Fatalf("content = %q, want %q", b, blob)
	}
}

// A hard-link member with an absolute link name inside the layer keeps extracting.
func TestAbsoluteHardLinkInsideExtracts(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	target := filepath.Join(workDir, title, "f.txt")
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/f.txt", Body: "hello world", Type: tar.TypeReg},
		{Name: title + "/hl", Link: target, Type: tar.TypeLink},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Fatalf("Push: %v", err)
	}
	if b := readOrFail(t, filepath.Join(workDir, title, "hl")); string(b) != "hello world" {
		t.Fatalf("content = %q", b)
	}
}

// An ordinary archive extracts in full, directories and files alike.
func TestOrdinaryLayerExtracts(t *testing.T) {
	workDir := t.TempDir()
	const title = "layer"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/a/", Type: tar.TypeDir},
		{Name: title + "/a/x.txt", Body: "x-content", Type: tar.TypeReg},
		{Name: title + "/b.txt", Body: "b-content", Type: tar.TypeReg},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Fatalf("Push: %v", err)
	}
	if b := readOrFail(t, filepath.Join(workDir, title, "a", "x.txt")); string(b) != "x-content" {
		t.Fatalf("a/x.txt = %q", b)
	}
	if b := readOrFail(t, filepath.Join(workDir, title, "b.txt")); string(b) != "b-content" {
		t.Fatalf("b.txt = %q", b)
	}
}

// An ordinary push into a subdirectory keeps writing exactly where it says.
func TestOrdinaryPushInsideRoot(t *testing.T) {
	workDir := t.TempDir()
	blob := []byte("ordinary-content")
	if err := sup.Push(t, sup.StoreAt(t, workDir), "sub/file.txt", blob, false); err != nil {
		t.Fatalf("Push: %v", err)
	}
	if b := readOrFail(t, filepath.Join(workDir, "sub", "file.txt")); !bytes.Equal(b, blob) {
		t.Fatalf("content = %q, want %q", b, blob)
	}
}
