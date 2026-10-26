package vtesting

import (
	"testing"

	"github.com/go-git/go-git/v6/plumbing"
)

func TestFunc_Reflogs(t *testing.T) {
	_, r := newBareRepo(t)
	if err := r.Storer.SetReference(plumbing.NewHashReference("refs/heads/main", testHash())); err != nil {
		t.Fatalf("creating a branch: %v", err)
	}
	rs := reflogStorer(t, r)
	for _, name := range []plumbing.ReferenceName{"HEAD", "refs/heads/main"} {
		if err := rs.AppendReflog(name, testReflogEntry()); err != nil {
			t.Fatalf("appending a reflog entry for %q: %v", name, err)
		}
		entries, err := rs.Reflog(name)
		if err != nil {
			t.Fatalf("reading the reflog for %q: %v", name, err)
		}
		if len(entries) != 1 || entries[0].NewHash != testHash() {
			t.Fatalf("reflog for %q returned %d entries", name, len(entries))
		}
		if err := rs.DeleteReflog(name); err != nil {
			t.Fatalf("deleting the reflog for %q: %v", name, err)
		}
		entries, err = rs.Reflog(name)
		if err != nil {
			t.Fatalf("reading the reflog for %q after deletion: %v", name, err)
		}
		if len(entries) != 0 {
			t.Fatalf("reflog for %q still has %d entries", name, len(entries))
		}
	}
}
