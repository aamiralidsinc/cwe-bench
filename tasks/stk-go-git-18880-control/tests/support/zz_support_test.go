package vtesting

import (
	"os"
	"path/filepath"
	"testing"

	git "github.com/go-git/go-git/v6"
	"github.com/go-git/go-billy/v6"
	"github.com/go-git/go-billy/v6/osfs"
	"github.com/go-git/go-git/v6/plumbing"
	"github.com/go-git/go-git/v6/plumbing/cache"
	"github.com/go-git/go-git/v6/plumbing/format/reflog"
	"github.com/go-git/go-git/v6/plumbing/storer"
	"github.com/go-git/go-git/v6/storage/filesystem"
)

const testHashHex = "e8d3ffab552895c19b9fcf7aa264d277cde33881"

func testHash() plumbing.Hash { return plumbing.NewHash(testHashHex) }

func newHashReference(name string) *plumbing.Reference {
	return plumbing.NewHashReference(plumbing.ReferenceName(name), testHash())
}

// newBareRepo returns a bare repository whose metadata directory is dir.
func newBareRepo(t *testing.T) (string, *git.Repository) {
	t.Helper()
	dir := t.TempDir()
	r, err := git.PlainInit(dir, true)
	if err != nil {
		t.Fatalf("initialising a repository: %v", err)
	}
	t.Cleanup(func() { _ = r.Close() })
	return dir, r
}

// noReadWriteFS advertises a filesystem that cannot open files read-write. The
// storage layer supports such backends through its second implementation.
type noReadWriteFS struct{ billy.Filesystem }

func (f noReadWriteFS) Capabilities() billy.Capability {
	return billy.Capabilities(f.Filesystem) &^ billy.ReadAndWriteCapability
}

func newRepoOnNoReadWriteFS(t *testing.T) (string, *git.Repository) {
	t.Helper()
	dir := t.TempDir()
	st := filesystem.NewStorage(noReadWriteFS{osfs.New(dir)}, cache.NewObjectLRUDefault())
	r, err := git.Init(st)
	if err != nil {
		t.Fatalf("initialising a repository on a read-only-capable filesystem: %v", err)
	}
	t.Cleanup(func() { _ = r.Close() })
	return dir, r
}

func writeFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("creating parent directory for %s: %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("writing %s: %v", path, err)
	}
}

func readFile(t *testing.T, path string) string {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("reading %s: %v", path, err)
	}
	return string(b)
}

func requireUnchanged(t *testing.T, path, want string) {
	t.Helper()
	if got := readFile(t, path); got != want {
		t.Fatalf("%s changed by an operation that must have no effect: got %q, want %q", path, got, want)
	}
}

// requireRefused asserts that a name was refused. It deliberately does not
// require a particular error value or status: any error is a refusal.
func requireRefused(t *testing.T, err error) {
	t.Helper()
	if err == nil {
		t.Fatalf("an unsafe reference name was accepted; want a refusal")
	}
}

func reflogStorer(t *testing.T, r *git.Repository) storer.ReflogStorer {
	t.Helper()
	rs, ok := r.Storer.(storer.ReflogStorer)
	if !ok {
		t.Fatalf("the storage does not expose reflog operations")
	}
	return rs
}

func testReflogEntry() *reflog.Entry {
	return &reflog.Entry{
		OldHash:   plumbing.ZeroHash,
		NewHash:   testHash(),
		Committer: reflog.Signature{Name: "A U Thor", Email: "author@example.com"},
		Message:   "commit: initial",
	}
}

const validReflogLine = "0000000000000000000000000000000000000000 " +
	testHashHex + " A U Thor <author@example.com> 1700000000 +0000\tcommit: initial\n"
