package vtesting

import (
	"path/filepath"
	"testing"
)

// Removing a reference must not let its name remove the repository configuration.
func TestSec_DeleteDoesNotRemoveConfig(t *testing.T) {
	dir, r := newBareRepo(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := r.Storer.RemoveReference("config")
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}

// A parent-path component must not let a removal reach packed references.
func TestSec_DeleteRejectsTraversalName(t *testing.T) {
	dir, r := newBareRepo(t)
	packed := filepath.Join(dir, "packed-refs")
	writeFile(t, packed, "packed-references-marker")

	err := r.Storer.RemoveReference("refs/../../packed-refs")
	requireRefused(t, err)
	requireUnchanged(t, packed, "packed-references-marker")
}
