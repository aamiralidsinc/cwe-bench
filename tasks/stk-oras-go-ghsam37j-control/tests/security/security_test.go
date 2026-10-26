package htests_security

import (
	"archive/tar"
	"path/filepath"
	"strings"
	"testing"

	sup "oras.land/oras-go/v2/htests_support"
)

const hostilePayload = "PWNED-BY-UNTRUSTED-ARCHIVE"

func chainEntries(title, prefix, outsidePath string, depth int) []sup.Entry {
	dirs := make([]string, depth)
	for i := range dirs {
		dirs[i] = "d"
	}
	rel := strings.Join(dirs, "/")
	var ents []sup.Entry
	for i := 1; i <= depth; i++ {
		ents = append(ents, sup.Entry{Name: title + "/" + prefix + strings.Join(dirs[:i], "/"), Type: tar.TypeDir})
	}
	upName := title + "/" + prefix + rel + "/up"
	if prefix == "" {
		ents = append(ents, sup.Entry{Name: upName, Link: strings.Repeat("../", depth-1) + "..", Type: tar.TypeSymlink})
	} else {
		ents = append(ents, sup.Entry{Name: upName, Link: strings.Repeat("../", depth) + "..", Type: tar.TypeSymlink})
	}
	escapeName := title + "/" + prefix + "escape"
	target := rel + "/up/" + strings.Repeat("../", depth-1) + ".."
	if prefix != "" {
		target = rel + "/up/" + strings.Repeat("../", depth) + ".."
	}
	target += outsidePath
	ents = append(ents, sup.Entry{Name: escapeName, Link: target, Type: tar.TypeSymlink})
	ents = append(ents, sup.Entry{Name: escapeName, Body: hostilePayload, Type: tar.TypeReg})
	return ents
}

func depthOf(abs string) int {
	return len(strings.Split(strings.Trim(filepath.ToSlash(abs), "/"), "/"))
}

func assertContained(t *testing.T, workDir, outsidePath string) {
	if b, ok, err := sup.ReadFile(outsidePath); err != nil {
		t.Fatal(err)
	} else if ok {
		t.Fatalf("extraction wrote outside the working directory: %q", b)
	}
}

func TestExtractSymlinkChainEscape(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "out"
	blob := sup.TarGz(t, chainEntries(title, "", outsidePath, depthOf(filepath.Join(workDir, title))))
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v", err)
	}
	assertContained(t, workDir, outsidePath)
}

func TestExtractSymlinkChainEscapeRelativeRoot(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	t.Chdir(workDir)
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "out"
	blob := sup.TarGz(t, chainEntries(title, "", outsidePath, depthOf(filepath.Join(workDir, title))))
	if err := sup.Push(t, sup.StoreAt(t, "."), title, blob, true); err != nil {
		t.Logf("Push returned %v", err)
	}
	assertContained(t, workDir, outsidePath)
}

func TestExtractSymlinkChainEscapeMultiComponentTitle(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "a/b"
	blob := sup.TarGz(t, chainEntries(title, "", outsidePath, depthOf(filepath.Join(workDir, title))))
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v", err)
	}
	assertContained(t, workDir, outsidePath)
}

func TestExtractSymlinkChainEscapeNested(t *testing.T) {
	workDir, outsideDir := t.TempDir(), t.TempDir()
	outsidePath := filepath.Join(outsideDir, "PWNED")
	const title = "out"
	blob := sup.TarGz(t, chainEntries(title, "sub/", outsidePath, depthOf(filepath.Join(workDir, title))))
	if err := sup.Push(t, sup.StoreAt(t, workDir), title, blob, true); err != nil {
		t.Logf("Push returned %v", err)
	}
	assertContained(t, workDir, outsidePath)
}
