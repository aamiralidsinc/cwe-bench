//go:build unix

package plugin_test

import (
	"os"
	"path/filepath"
	"testing"

	v1 "github.com/google/go-containerregistry/pkg/v1"
	"github.com/stretchr/testify/require"

	ftypes "github.com/aquasecurity/trivy/pkg/fanal/types"
	"github.com/aquasecurity/trivy/pkg/plugin"
)

// vHome points XDG_DATA_HOME at a fresh temp dir and returns it together with
// the plugin root directory under it.
func vHome(t *testing.T) (home, root string) {
	home = t.TempDir()
	t.Setenv("XDG_DATA_HOME", home)
	root = filepath.Join(home, ".trivy", "plugins")
	require.NoError(t, os.MkdirAll(root, 0o755))
	return home, root
}

// writeSrcPlugin creates an installable plugin source directory whose metadata
// declares the given name.
func writeSrcPlugin(t *testing.T, dir, name string) {
	require.NoError(t, os.MkdirAll(dir, 0o755))
	yaml := "name: \"" + name + "\"\nrepository: testsrc\nversion: \"0.1.0\"\nsummary: test\ndescription: test\nplatforms:\n  - selector:\n      os: linux\n      arch: amd64\n    uri: ./test.sh\n    bin: ./test.sh\n"
	require.NoError(t, os.WriteFile(filepath.Join(dir, "plugin.yaml"), []byte(yaml), 0o644))
	require.NoError(t, os.WriteFile(filepath.Join(dir, "test.sh"), []byte("#!/bin/sh\necho hi\n"), 0o755))
}

// setupInstalled writes an already-installed plugin under root in directory
// dirName, whose stored metadata records storedName as its name.
func setupInstalled(t *testing.T, root, dirName, storedName string) {
	d := filepath.Join(root, dirName)
	require.NoError(t, os.MkdirAll(d, 0o755))
	yaml := "name: \"" + storedName + "\"\nrepository: testsrc\nversion: \"0.1.0\"\nusage: test\ndescription: test\nplatforms:\n  - selector:\n      os: linux\n      arch: amd64\n    uri: ./test.sh\n    bin: ./test.sh\ninstalled:\n  platform:\n    os: linux\n    arch: amd64\n"
	require.NoError(t, os.WriteFile(filepath.Join(d, "plugin.yaml"), []byte(yaml), 0o644))
	require.NoError(t, os.WriteFile(filepath.Join(d, "test.sh"), []byte("#!/bin/sh\n"), 0o755))
}

func instOpts() plugin.Options {
	return plugin.Options{Platform: ftypes.Platform{Platform: &v1.Platform{Architecture: "amd64", OS: "linux"}}}
}
