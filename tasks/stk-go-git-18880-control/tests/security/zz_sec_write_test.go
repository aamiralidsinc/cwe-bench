package vtesting

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/go-git/go-git/v6/plumbing"
)

// Storing a reference must not let its name reach the repository configuration.
func TestSec_WriteDoesNotOverwriteConfig(t *testing.T) {
	dir, r := newBareRepo(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := r.Storer.SetReference(plumbing.NewHashReference("config", testHash()))
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}

// A name carrying a parent-path component must not resolve onto configuration
// that lives next to the reference tree.
func TestSec_WriteRejectsTraversalName(t *testing.T) {
	dir, r := newBareRepo(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := r.Storer.SetReference(plumbing.NewHashReference("refs/../../config", testHash()))
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}

// A name must not create files in the repository's hook directory.
func TestSec_WriteDoesNotCreateHook(t *testing.T) {
	dir, r := newBareRepo(t)
	hook := filepath.Join(dir, "hooks", "pre-commit")

	err := r.Storer.SetReference(plumbing.NewHashReference("hooks/pre-commit", testHash()))
	requireRefused(t, err)
	if _, statErr := os.Stat(hook); statErr == nil {
		t.Fatalf("a reference write created %s", hook)
	}
}

// The same protection must hold for a filesystem that takes the storage's
// second, simpler write implementation.
func TestSec_WriteSecondImplementation(t *testing.T) {
	dir, r := newRepoOnNoReadWriteFS(t)
	config := filepath.Join(dir, "config")
	writeFile(t, config, "repository-configuration-marker")

	err := r.Storer.SetReference(plumbing.NewHashReference("refs/../../config", testHash()))
	requireRefused(t, err)
	requireUnchanged(t, config, "repository-configuration-marker")
}
