package vtesting

import (
	"path/filepath"
	"testing"
)

// Appending a reflog entry must not write into the repository configuration.
func TestSec_ReflogAppendDoesNotWriteMetadata(t *testing.T) {
	dir, r := newBareRepo(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := reflogStorer(t, r).AppendReflog("refs/../../config", testReflogEntry())
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}

// Reading a reflog must not return the contents of unrelated repository metadata.
func TestSec_ReflogReadDoesNotReturnMetadata(t *testing.T) {
	dir, r := newBareRepo(t)
	writeFile(t, filepath.Join(dir, "hooks", "post-checkout"), validReflogLine)

	entries, err := reflogStorer(t, r).Reflog("../hooks/post-checkout")
	requireRefused(t, err)
	if len(entries) != 0 {
		t.Fatalf("a metadata file was returned as a reflog with %d entries", len(entries))
	}
}

// Deleting a reflog must not remove unrelated repository metadata.
func TestSec_ReflogDeleteDoesNotRemoveMetadata(t *testing.T) {
	dir, r := newBareRepo(t)
	hook := filepath.Join(dir, "hooks", "post-checkout")
	writeFile(t, hook, "hook-marker")

	err := reflogStorer(t, r).DeleteReflog("../hooks/post-checkout")
	requireRefused(t, err)
	requireUnchanged(t, hook, "hook-marker")
}
