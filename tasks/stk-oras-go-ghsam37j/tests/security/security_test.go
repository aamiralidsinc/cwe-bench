// Package htests_security drives the file store's public entry points against untrusted
// artifacts and asserts that nothing is created or changed outside the store's working directory.
package htests_security

import (
	"archive/tar"
	"os"
	"path/filepath"
	"strings"
	"testing"

	sup "oras.land/oras-go/v2/htests_support"
)

const hostilePayload = "PWNED-BY-UNTRUSTED-ARCHIVE"

// chainEntries builds the archive reported in the advisory: a chain of symlinks whose lexical
// target stays inside the extraction root but whose kernel-resolved target is outsidePath, then a
// regular member with the same name that is written through the last link.
func chainEntries(title, outsidePath string, depth int) []sup.Entry {
	dirs := make([]string, depth)
	for i := range dirs {
		dirs[i] = "d"
	}
	var ents []sup.Entry
	for i := 1; i <= depth; i++ {
		ents = append(ents, sup.Entry{
			Name: title + "/" + strings.Join(dirs[:i], "/"),
			Type: tar.TypeDir,
		})
	}
	ents = append(ents, sup.Entry{
		Name: title + "/" + strings.Join(dirs, "/") + "/up",
		Link: strings.Repeat("../", depth-1) + "..",
		Type: tar.TypeSymlink,
	})
	escapeTarget := strings.Join(dirs, "/") + "/up/" + strings.Repeat("../", depth-1) + ".." + outsidePath
	ents = append(ents, sup.Entry{
		Name: title + "/escape",
		Link: escapeTarget,
		Type: tar.TypeSymlink,
	})
	ents = append(ents, sup.Entry{
		Name: title + "/escape",
		Body: hostilePayload,
		Type: tar.TypeReg,
	})
	return ents
}

func depthOf(abs string) int {
	return len(strings.Split(strings.Trim(filepath.ToSlash(abs), "/"), "/"))
}

// T1: a chain of links inside the extraction root resolves outside it; a same-named regular
// member writes through the chain. Nothing may appear at the attacker's outside path.
func TestExtractSymlinkChainEscape(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "out"
	baseAbs := filepath.Join(workDir, title)

	blob := sup.TarGz(t, chainEntries(title, outsidePath, depthOf(baseAbs)))
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, ok, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if ok {
		t.Fatalf("extraction wrote outside the working directory: %q", b)
	}
}

// T1, relative-root form: the store's working directory is a relative path.
func TestExtractSymlinkChainEscapeRelativeRoot(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	t.Chdir(workDir)
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "out"

	// The archive climbs from the extraction root to the filesystem root, so the depth is the
	// absolute root's component count even though the store was opened with ".".
	blob := sup.TarGz(t, chainEntries(title, outsidePath, depthOf(filepath.Join(workDir, title))))
	if err := sup.Push(t, sup.StoreAt(t, "."), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, ok, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if ok {
		t.Fatalf("extraction wrote outside the working directory: %q", b)
	}
}

// T2, root-level form: a link that already sits at a member's final path is followed when the
// regular member is written.
func TestExtractTerminalSymlinkWriteThrough(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	const title = "title"
	outsidePath := filepath.Join(outsideDir, "victim.txt")
	if err := os.WriteFile(outsidePath, []byte("ORIGINAL"), 0o644); err != nil {
		t.Fatal(err)
	}
	layerDir := filepath.Join(workDir, title)
	if err := os.MkdirAll(layerDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outsidePath, filepath.Join(layerDir, "escape")); err != nil {
		t.Fatal(err)
	}

	blob := sup.TarGz(t, []sup.Entry{{Name: title + "/escape", Body: hostilePayload, Type: tar.TypeReg}})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, _, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if string(b) != "ORIGINAL" {
		t.Fatalf("regular member was written through a link outside the working directory: %q", b)
	}
}

// T2, nested form: the same shape one directory deeper, so the final component is still the one
// the walk does not inspect.
func TestExtractTerminalSymlinkNestedWriteThrough(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	const title = "title"
	outsidePath := filepath.Join(outsideDir, "victim.txt")
	if err := os.WriteFile(outsidePath, []byte("ORIGINAL"), 0o644); err != nil {
		t.Fatal(err)
	}
	subDir := filepath.Join(workDir, title, "sub")
	if err := os.MkdirAll(subDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outsidePath, filepath.Join(subDir, "escape")); err != nil {
		t.Fatal(err)
	}

	blob := sup.TarGz(t, []sup.Entry{{Name: title + "/sub/escape", Body: hostilePayload, Type: tar.TypeReg}})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, _, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if string(b) != "ORIGINAL" {
		t.Fatalf("regular member was written through a link outside the working directory: %q", b)
	}
}

// T4: a member name that traverses a directory link in the store root must not write outside it.
func TestPushSymlinkComponentEscape(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	if err := os.Symlink(outsideDir, filepath.Join(workDir, "out")); err != nil {
		t.Fatal(err)
	}
	blob := []byte(hostilePayload)
	if err := sup.Push(t, sup.StoreAt(t, workDir), "out/secret.txt", blob, false); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, ok, err := sup.ReadFile(filepath.Join(outsideDir, "secret.txt")); err != nil {
		t.Fatal(err)
	} else if ok {
		t.Fatalf("push wrote outside the working directory: %q", b)
	}
}

// T4, unpack form: the layer directory itself would be created through the same link.
func TestPushSymlinkComponentUnpackEscape(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	if err := os.Symlink(outsideDir, filepath.Join(workDir, "out")); err != nil {
		t.Fatal(err)
	}
	const title = "out/layer"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/f.txt", Body: hostilePayload, Type: tar.TypeReg},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, ok, err := sup.ReadFile(filepath.Join(outsideDir, "layer", "f.txt")); err != nil {
		t.Fatal(err)
	} else if ok {
		t.Fatalf("unpack wrote outside the working directory: %q", b)
	}
}

// T3: a relative hard-link member name is applied against the process working directory; the
// resulting member aliases a file outside the store, and a later member writes through it.
func TestExtractHardLinkAliasesOutsideFile(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "victim")
	if err := os.WriteFile(outsidePath, []byte("ORIGINAL"), 0o644); err != nil {
		t.Fatal(err)
	}
	t.Chdir(outsideDir)
	const title = "title"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/hl", Link: "victim", Type: tar.TypeLink},
		{Name: title + "/hl", Body: hostilePayload, Type: tar.TypeReg},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	if b, _, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if string(b) != "ORIGINAL" {
		t.Fatalf("hard-link member aliased a file outside the working directory: %q", b)
	}
}

// T3: even without the later write, an extracted member must not be the same file as one that
// lies outside the store.
func TestExtractHardLinkAliasWithoutWrite(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "victim")
	if err := os.WriteFile(outsidePath, []byte("ORIGINAL"), 0o644); err != nil {
		t.Fatal(err)
	}
	t.Chdir(outsideDir)
	const title = "title"
	blob := sup.TarGz(t, []sup.Entry{
		{Name: title + "/", Type: tar.TypeDir},
		{Name: title + "/hl", Link: "victim", Type: tar.TypeLink},
	})
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v (an error is acceptable)", err)
	}
	outsideInfo, err := os.Stat(outsidePath)
	if err != nil {
		t.Fatal(err)
	}
	extractedInfo, err := os.Stat(filepath.Join(workDir, title, "hl"))
	if err != nil {
		if os.IsNotExist(err) {
			return // the member was refused; nothing aliases the outside file
		}
		t.Fatal(err)
	}
	if os.SameFile(outsideInfo, extractedInfo) {
		t.Fatalf("extracted member %q is the same file as %q outside the store", extractedInfo.Name(), outsidePath)
	}
}
