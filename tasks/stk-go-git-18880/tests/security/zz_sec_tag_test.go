package vtesting

import (
	"path/filepath"
	"testing"

	"github.com/go-git/go-git/v6/plumbing"
)

// A short name given for one reference kind must not select another reference.
func TestSec_TagDoesNotReturnOtherReference(t *testing.T) {
	_, r := newBareRepo(t)
	if err := r.Storer.SetReference(plumbing.NewHashReference("refs/heads/main", testHash())); err != nil {
		t.Fatalf("creating a branch: %v", err)
	}

	ref, err := r.Tag("../heads/main")
	requireRefused(t, err)
	if ref != nil {
		t.Fatalf("a branch was returned as a tag: %q", ref.Name())
	}
}

// Deleting by a short name must not delete another reference.
func TestSec_DeleteTagDoesNotDeleteBranch(t *testing.T) {
	_, r := newBareRepo(t)
	if err := r.Storer.SetReference(plumbing.NewHashReference("refs/heads/main", testHash())); err != nil {
		t.Fatalf("creating a branch: %v", err)
	}

	err := r.DeleteTag("../heads/main")
	requireRefused(t, err)
	if _, refErr := r.Storer.Reference("refs/heads/main"); refErr != nil {
		t.Fatalf("a branch was removed by a tag deletion: %v", refErr)
	}
}

// A short name carrying a parent-path component must not remove repository metadata.
func TestSec_DeleteTagDoesNotRemoveMetadata(t *testing.T) {
	dir, r := newBareRepo(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := r.DeleteTag("../../config")
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}
