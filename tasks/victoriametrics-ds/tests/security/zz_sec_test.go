package actions_test

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/actions"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/backupnames"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/common"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/fslocal"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/fsremote"
)

func secNewRestore(t *testing.T, dstDir string, src *secTestRemote) *actions.Restore {
	t.Helper()
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	dst := &fslocal.FS{Dir: dstDir}
	if err := dst.Init(); err != nil {
		t.Fatalf("cannot init destination: %s", err)
	}
	t.Cleanup(dst.MustStop)
	return &actions.Restore{
		Concurrency:             1,
		Src:                     src,
		Dst:                     dst,
		SkipBackupCompleteCheck: true,
	}
}

func secRequireAbsent(t *testing.T, path string) {
	t.Helper()
	if _, err := os.Lstat(path); err == nil {
		t.Fatalf("a path outside the destination was created: %s", path)
	}
}

// A source that names a file above the destination directory must be refused and
// must leave nothing outside the destination.
func TestSecRestoreRejectsLeadingTraversal(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: secParts("../outside/marker.txt", 5)}
	r := secNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err == nil {
		t.Fatalf("restore from a source naming a path outside the destination succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "outside", "marker.txt"))
	secRequireAbsent(t, filepath.Join(root, "outside", "marker.txt.tmp"))
	secRequireAbsent(t, filepath.Join(root, "outside"))
}

// A traversal buried in the middle of a name must be refused.
func TestSecRestoreRejectsMidPathTraversal(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: secParts("a/../../outside/marker.txt", 5)}
	r := secNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err == nil {
		t.Fatalf("restore from a source naming a path outside the destination succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "outside", "marker.txt"))
	secRequireAbsent(t, filepath.Join(root, "outside"))
}

// A sibling whose absolute path shares the destination's character prefix is outside
// the destination and must be refused.
func TestSecRestoreRejectsPrefixSibling(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: secParts("../storagefoo/evil.txt", 5)}
	r := secNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err == nil {
		t.Fatalf("restore from a source naming a prefix-sharing sibling succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "storagefoo", "evil.txt"))
	secRequireAbsent(t, filepath.Join(root, "storagefoo"))
}

// A refusal must not leave a side effect (a directory or a temporary file) outside
// the destination: the operation has to decide before it reserves or creates space.
func TestSecRestoreRefusalLeavesNoSideEffect(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: secParts("../elsewhere/created.txt", 7)}
	r := secNewRestore(t, dstDir, src)

	err := r.Run(context.Background())
	if err == nil {
		t.Fatalf("restore from a source naming a path outside the destination succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "elsewhere"))
}

// A remote backup copy into a local destination must apply the same rule.
func TestSecCopyRejectsLeadingTraversal(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "backup")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	src := &secTestRemote{
		parts: secParts("../outside/marker.txt", 5),
		files: map[string][]byte{backupnames.BackupMetadataFilename: []byte(`{}`)},
	}
	a := &actions.RemoteBackupCopy{Concurrency: 1, Src: src, Dst: &fsremote.FS{Dir: dstDir}}

	if err := a.Run(); err == nil {
		t.Fatalf("remote copy from a source naming a path outside the destination succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "outside", "marker.txt"))
	secRequireAbsent(t, filepath.Join(root, "outside"))
}

// The prefix-sharing sibling rule also applies to a remote backup copy.
func TestSecCopyRejectsPrefixSibling(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "backup")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	src := &secTestRemote{
		parts: secParts("../backupfoo/evil.txt", 5),
		files: map[string][]byte{backupnames.BackupMetadataFilename: []byte(`{}`)},
	}
	a := &actions.RemoteBackupCopy{Concurrency: 1, Src: src, Dst: &fsremote.FS{Dir: dstDir}}

	if err := a.Run(); err == nil {
		t.Fatalf("remote copy from a source naming a prefix-sharing sibling succeeded")
	}
	secRequireAbsent(t, filepath.Join(root, "backupfoo", "evil.txt"))
	secRequireAbsent(t, filepath.Join(root, "backupfoo"))
}

// Metadata carried by the backup source must not name a local path outside the
// destination directory.
func TestSecCopyServiceFileStaysInside(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "backup")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	src := &secTestRemote{
		files: map[string][]byte{
			backupnames.BackupMetadataFilename: []byte(`{"service_files":["../outside/marker.txt"]}`),
			"../outside/marker.txt":            []byte("marker"),
		},
	}
	a := &actions.RemoteBackupCopy{Concurrency: 1, Src: src, Dst: &fsremote.FS{Dir: dstDir}}

	if err := a.Run(); err == nil {
		t.Fatalf("remote copy wrote a file named by backup metadata outside the destination")
	}
	secRequireAbsent(t, filepath.Join(root, "outside", "marker.txt"))
	secRequireAbsent(t, filepath.Join(root, "outside"))
}

// A path carried by the backup source in its excluded paths file must not remove a
// file outside the destination directory.
func TestSecRestoreExcludedPathsStaysInside(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	outsideDir := filepath.Join(root, "outside")
	if err := os.MkdirAll(outsideDir, 0700); err != nil {
		t.Fatalf("cannot create outside dir: %s", err)
	}
	marker := filepath.Join(outsideDir, "marker.txt")
	if err := os.WriteFile(marker, []byte("keep"), 0600); err != nil {
		t.Fatalf("cannot create marker: %s", err)
	}
	src := &secTestRemote{
		files: map[string][]byte{
			backupnames.ExcludedPathsFilename: []byte("../outside/marker.txt\n"),
		},
	}
	r := secNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err == nil {
		t.Fatalf("restore did not report an error for an excluded path outside the destination")
	}
	if _, err := os.Stat(marker); err != nil {
		t.Fatalf("a file outside the destination was removed: %s", err)
	}
}

func secParts(path string, size uint64) []common.Part {
	return []common.Part{secPart(path, size)}
}
