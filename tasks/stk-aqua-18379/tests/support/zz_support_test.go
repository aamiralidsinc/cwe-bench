package unarchive_test

// Shared harness for the hidden suites staged into pkg/unarchive at grading time.
// Everything here builds archives in memory and extracts them through the package's
// exported entry point, so the suites exercise the real handler end to end.

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"testing"

	"github.com/aquaproj/aqua/v2/pkg/download"
	"github.com/aquaproj/aqua/v2/pkg/unarchive"
	"github.com/spf13/afero"
)

type archiveEntry struct {
	name string
	typ  byte
	link string
	mode int64
	body []byte
}

func buildTarGz(t *testing.T, ents []archiveEntry) []byte {
	t.Helper()
	var buf bytes.Buffer
	gw := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gw)
	for _, e := range ents {
		typ := e.typ
		if typ == 0 {
			typ = tar.TypeReg
		}
		mode := e.mode
		if mode == 0 {
			if typ == tar.TypeDir {
				mode = 0o755
			} else {
				mode = 0o644
			}
		}
		h := &tar.Header{Name: e.name, Typeflag: typ, Linkname: e.link, Mode: mode, Size: int64(len(e.body))}
		if typ != tar.TypeReg {
			h.Size = 0
		}
		if err := tw.WriteHeader(h); err != nil {
			t.Fatal(err)
		}
		if typ == tar.TypeReg && len(e.body) > 0 {
			if _, err := tw.Write(e.body); err != nil {
				t.Fatal(err)
			}
		}
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	if err := gw.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func extractTarGz(data []byte, dest string) error {
	fs := afero.NewOsFs()
	src := &unarchive.File{
		Filename: "asset.tar.gz",
		Body:     download.NewDownloadedFile(fs, io.NopCloser(bytes.NewReader(data)), nil),
	}
	return unarchive.New(nil, fs).Unarchive(context.Background(), slog.New(slog.DiscardHandler), src, dest)
}

// fixtureDirs returns a parent directory, an empty install directory below it, and
// the path of a sibling "outside" directory that is not the install directory.
func fixtureDirs(t *testing.T) (parent, dest, outsideDir string) {
	t.Helper()
	parent = t.TempDir()
	dest = filepath.Join(parent, "dest")
	if err := os.MkdirAll(dest, 0o755); err != nil {
		t.Fatal(err)
	}
	outsideDir = filepath.Join(parent, "outside")
	if err := os.MkdirAll(outsideDir, 0o755); err != nil {
		t.Fatal(err)
	}
	return parent, dest, outsideDir
}

const sentinel = "SENTINEL_ORIGINAL_CONTENT"

// fixtureWithOutside returns the same layout with a sentinel file outside the install
// directory. The sentinel's path is the one an escaping entry is aimed at.
func fixtureWithOutside(t *testing.T) (parent, dest, outsideFile string) {
	t.Helper()
	parent, dest, outsideDir := fixtureDirs(t)
	outsideFile = filepath.Join(outsideDir, "target")
	if err := os.WriteFile(outsideFile, []byte(sentinel), 0o644); err != nil {
		t.Fatal(err)
	}
	return parent, dest, outsideFile
}

func requireSentinelIntact(t *testing.T, outsideFile string) {
	t.Helper()
	got, err := os.ReadFile(outsideFile)
	if err != nil {
		t.Fatalf("the outside file no longer exists: %v", err)
	}
	if string(got) != sentinel {
		t.Fatalf("a file outside the install directory was modified: %q", got)
	}
}

const overwrite = "OVERWRITTEN_PAYLOAD_0123456789"
