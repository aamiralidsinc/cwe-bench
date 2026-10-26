package actions_test

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/actions"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/backupnames"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/common"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/fslocal"
	"github.com/VictoriaMetrics/VictoriaMetrics/lib/backup/fsremote"
)

func funcNewRestore(t *testing.T, dstDir string, src *secTestRemote) *actions.Restore {
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

func funcRequireContent(t *testing.T, path string, size int) {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("cannot read restored file %q: %s", path, err)
	}
	if len(data) != size {
		t.Fatalf("unexpected restored size for %q: got %d; want %d", path, len(data), size)
	}
}

func TestFuncRestoreLegitimateParts(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: []common.Part{
		secPart("parts/a.bin", 4),
		secPart("data/b.bin", 6),
	}}
	r := funcNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err != nil {
		t.Fatalf("restore of legitimate parts failed: %s", err)
	}
	funcRequireContent(t, filepath.Join(dstDir, "parts", "a.bin"), 4)
	funcRequireContent(t, filepath.Join(dstDir, "data", "b.bin"), 6)
}

// Names that contain ".." components but resolve inside the destination keep working.
func TestFuncRestoreLegitimateDotDotNames(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{parts: []common.Part{
		secPart("..foo.txt", 3),
		secPart("foo/../bar/file.dat", 5),
		secPart("/leading.txt", 7),
	}}
	r := funcNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err != nil {
		t.Fatalf("restore of legitimate in-directory names failed: %s", err)
	}
	funcRequireContent(t, filepath.Join(dstDir, "..foo.txt"), 3)
	funcRequireContent(t, filepath.Join(dstDir, "bar", "file.dat"), 5)
	funcRequireContent(t, filepath.Join(dstDir, "leading.txt"), 7)
	if _, err := os.Lstat(filepath.Join(dstDir, "foo")); err == nil {
		t.Fatalf("restore created an intermediate directory for a name that resolves inside: %q", filepath.Join(dstDir, "foo"))
	}
}

// A destination directory with a trailing separator keeps working.
func TestFuncRestoreDirTrailingSlash(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	dst := &fslocal.FS{Dir: dstDir + string(filepath.Separator)}
	if err := dst.Init(); err != nil {
		t.Fatalf("cannot init destination: %s", err)
	}
	t.Cleanup(dst.MustStop)
	src := &secTestRemote{parts: []common.Part{secPart("parts/a.bin", 4)}}
	r := &actions.Restore{Concurrency: 1, Src: src, Dst: dst, SkipBackupCompleteCheck: true}

	if err := r.Run(context.Background()); err != nil {
		t.Fatalf("restore into a destination with a trailing separator failed: %s", err)
	}
	funcRequireContent(t, filepath.Join(dstDir, "parts", "a.bin"), 4)
}

// Split parts of one file are reassembled, and destination files absent from the
// source are still deleted.
func TestFuncRestoreSplitPartsAndIncrementalDelete(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	staleDir := filepath.Join(dstDir, "stale")
	if err := os.MkdirAll(staleDir, 0700); err != nil {
		t.Fatalf("cannot create stale dir: %s", err)
	}
	if err := os.WriteFile(filepath.Join(staleDir, "old.bin"), []byte("old"), 0600); err != nil {
		t.Fatalf("cannot create stale file: %s", err)
	}
	src := &secTestRemote{parts: []common.Part{
		{Path: "big/data.bin", FileSize: 8, Offset: 0, Size: 4, ActualSize: 4},
		{Path: "big/data.bin", FileSize: 8, Offset: 4, Size: 4, ActualSize: 4},
		secPart("keep/new.bin", 5),
	}}
	r := funcNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err != nil {
		t.Fatalf("restore of split parts failed: %s", err)
	}
	funcRequireContent(t, filepath.Join(dstDir, "big", "data.bin"), 8)
	funcRequireContent(t, filepath.Join(dstDir, "keep", "new.bin"), 5)
	if _, err := os.Lstat(filepath.Join(staleDir, "old.bin")); err == nil {
		t.Fatalf("a destination file absent from the source was not deleted")
	}
}

// A legitimate excluded-path entry inside the destination is applied after restore.
func TestFuncRestoreExcludedPathsInside(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "storage")
	src := &secTestRemote{
		parts: []common.Part{
			secPart("data/secret.bin", 5),
			secPart("data/public.bin", 5),
		},
		files: map[string][]byte{
			backupnames.ExcludedPathsFilename: []byte("data/secret.bin\n"),
		},
	}
	r := funcNewRestore(t, dstDir, src)

	if err := r.Run(context.Background()); err != nil {
		t.Fatalf("restore with a legitimate excluded path failed: %s", err)
	}
	if _, err := os.Lstat(filepath.Join(dstDir, "data", "secret.bin")); err == nil {
		t.Fatalf("an excluded path was left in the restored data")
	}
	funcRequireContent(t, filepath.Join(dstDir, "data", "public.bin"), 5)
}

func funcPartFilePath(dstDir string, p common.Part) string {
	name := fmt.Sprintf("%016X_%016X_%016X", p.FileSize, p.Offset, p.Size)
	return filepath.Join(dstDir, p.Path, name)
}

func TestFuncCopyLegitimateParts(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "backup")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	p := secPart("parts/a.bin", 4)
	metadata := []byte(`{"created_at":"2026-01-01T00:00:00Z","completed_at":"2026-01-01T00:00:01Z"}`)
	src := &secTestRemote{
		parts: []common.Part{p},
		files: map[string][]byte{
			backupnames.BackupMetadataFilename: metadata,
		},
	}
	a := &actions.RemoteBackupCopy{Concurrency: 1, Src: src, Dst: &fsremote.FS{Dir: dstDir}}

	if err := a.Run(); err != nil {
		t.Fatalf("remote copy of legitimate parts failed: %s", err)
	}
	funcRequireContent(t, funcPartFilePath(dstDir, p), 4)
	funcRequireContent(t, filepath.Join(dstDir, backupnames.BackupMetadataFilename), len(metadata))
	if _, err := os.Stat(filepath.Join(dstDir, backupnames.BackupCompleteFilename)); err != nil {
		t.Fatalf("the copy did not record a complete backup: %s", err)
	}
}

// A legitimate service file recorded in the metadata is preserved by the copy.
func TestFuncCopyServiceFileInside(t *testing.T) {
	root := t.TempDir()
	dstDir := filepath.Join(root, "backup")
	if err := os.MkdirAll(dstDir, 0700); err != nil {
		t.Fatalf("cannot create destination: %s", err)
	}
	src := &secTestRemote{
		files: map[string][]byte{
			backupnames.BackupMetadataFilename: []byte(`{"service_files":["backup_locked.ignore"]}`),
			backupnames.ProtectMarkFileName:    []byte("locked"),
		},
	}
	a := &actions.RemoteBackupCopy{Concurrency: 1, Src: src, Dst: &fsremote.FS{Dir: dstDir}}

	if err := a.Run(); err != nil {
		t.Fatalf("remote copy with a legitimate service file failed: %s", err)
	}
	funcRequireContent(t, filepath.Join(dstDir, backupnames.ProtectMarkFileName), 6)
}
