// Package htests_support holds setup helpers for the behavioural suites. It never computes an
// expected value with product code: paths, bytes and archive members are built here with the
// standard library only.
package htests_support

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"os"
	"testing"

	"github.com/opencontainers/go-digest"
	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	"oras.land/oras-go/v2/content/file"
)

// Entry is one member of a synthetic layer archive.
type Entry struct {
	Name string
	Link string
	Body string
	Type byte
	Mode int64
}

// TarGz builds a gzip-compressed tar from entries.
func TarGz(t *testing.T, entries []Entry) []byte {
	t.Helper()
	var buf bytes.Buffer
	gzw := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gzw)
	for _, e := range entries {
		mode := e.Mode
		if mode == 0 {
			mode = 0o755
		}
		h := &tar.Header{Typeflag: e.Type, Name: e.Name, Linkname: e.Link, Mode: mode}
		if e.Type == tar.TypeReg {
			h.Size = int64(len(e.Body))
			if e.Mode == 0 {
				h.Mode = 0o644
			}
		}
		if err := tw.WriteHeader(h); err != nil {
			t.Fatalf("write tar header %q: %v", e.Name, err)
		}
		if e.Type == tar.TypeReg {
			if _, err := tw.Write([]byte(e.Body)); err != nil {
				t.Fatalf("write tar body %q: %v", e.Name, err)
			}
		}
	}
	if err := tw.Close(); err != nil {
		t.Fatalf("close tar: %v", err)
	}
	if err := gzw.Close(); err != nil {
		t.Fatalf("close gzip: %v", err)
	}
	return buf.Bytes()
}

// StoreAt opens a file store rooted at root.
func StoreAt(t *testing.T, root string) *file.Store {
	t.Helper()
	s, err := file.New(root)
	if err != nil {
		t.Fatalf("open store at %s: %v", root, err)
	}
	t.Cleanup(func() { _ = s.Close() })
	return s
}

// Push writes blob as a member named name. When unpack is true the blob is treated as a layer
// archive and extracted into the store.
func Push(t *testing.T, s *file.Store, name string, blob []byte, unpack bool) error {
	t.Helper()
	desc := ocispec.Descriptor{
		MediaType: ocispec.MediaTypeImageLayerGzip,
		Digest:    digest.FromBytes(blob),
		Size:      int64(len(blob)),
		Annotations: map[string]string{
			ocispec.AnnotationTitle: name,
		},
	}
	if unpack {
		desc.Annotations[file.AnnotationUnpack] = "true"
	}
	return s.Push(context.Background(), desc, bytes.NewReader(blob))
}

// ReadFile returns the file's content, or ok=false if it does not exist.
func ReadFile(path string) ([]byte, bool, error) {
	b, err := os.ReadFile(path)
	if err == nil {
		return b, true, nil
	}
	if os.IsNotExist(err) {
		return nil, false, nil
	}
	return nil, false, err
}
