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

// dsHome points XDG_DATA_HOME at a fresh directory and returns it with the
// plugin directory underneath it. An empty index is written so that no index
// download is attempted.
func dsHome(t *testing.T) (home, root string) {
	home = t.TempDir()
	t.Setenv("XDG_DATA_HOME", home)
	root = filepath.Join(home, ".trivy", "plugins")
	require.NoError(t, os.MkdirAll(root, 0o755))
	require.NoError(t, os.WriteFile(filepath.Join(root, "index.yaml"), []byte("version: 1\nplugins: []\n"), 0o644))
	return home, root
}

// dsSource creates a plugin source directory whose metadata declares name.
func dsSource(t *testing.T, name string) string {
	d := filepath.Join(t.TempDir(), "src")
	require.NoError(t, os.MkdirAll(d, 0o755))
	meta := "name: \"" + name + "\"\nrepository: testsrc\nversion: \"0.1.0\"\n" +
		"summary: test\ndescription: test\nplatforms:\n  - selector:\n      os: linux\n      arch: amd64\n" +
		"    uri: ./test.sh\n    bin: ./test.sh\n"
	require.NoError(t, os.WriteFile(filepath.Join(d, "plugin.yaml"), []byte(meta), 0o644))
	require.NoError(t, os.WriteFile(filepath.Join(d, "test.sh"), []byte("#!/bin/sh\nexit 0\n"), 0o755))
	return d
}

// dsInstalled creates an installed plugin in directory dirName whose stored
// metadata records storedName and runs bin.
func dsInstalled(t *testing.T, root, dirName, storedName, bin string) string {
	d := filepath.Join(root, dirName)
	require.NoError(t, os.MkdirAll(d, 0o755))
	meta := "name: \"" + storedName + "\"\nrepository: testsrc\nversion: \"0.1.0\"\n" +
		"summary: test\ndescription: test\nplatforms:\n  - selector:\n      os: linux\n      arch: amd64\n" +
		"    uri: ./" + bin + "\n    bin: ./" + bin + "\ninstalled:\n  platform:\n    os: linux\n    arch: amd64\n"
	require.NoError(t, os.WriteFile(filepath.Join(d, "plugin.yaml"), []byte(meta), 0o644))
	return d
}

func dsOpts() plugin.Options {
	return plugin.Options{Platform: ftypes.Platform{Platform: &v1.Platform{Architecture: "amd64", OS: "linux"}}}
}
