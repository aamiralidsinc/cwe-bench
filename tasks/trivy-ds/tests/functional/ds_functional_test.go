//go:build unix

// Functional tests: ordinary plugin management keeps working.

package plugin_test

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/aquasecurity/trivy/pkg/plugin"
)

func TestFunc_InstallLocal(t *testing.T) {
	_, root := dsHome(t)

	_, err := plugin.NewManager().Install(context.Background(), dsSource(t, "goodplugin"), dsOpts())

	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "goodplugin", "test.sh"))
	assert.FileExists(t, filepath.Join(root, "goodplugin", "plugin.yaml"))
}

func TestFunc_InstallNested(t *testing.T) {
	_, root := dsHome(t)
	parent := filepath.Join(t.TempDir(), "parent")
	require.NoError(t, os.MkdirAll(parent, 0o755))
	src := dsSource(t, "nestedplugin")
	require.NoError(t, os.Rename(src, filepath.Join(parent, "inner")))

	_, err := plugin.NewManager().Install(context.Background(), parent, dsOpts())

	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "nestedplugin", "test.sh"))
}

func TestFunc_UninstallExisting(t *testing.T) {
	_, root := dsHome(t)
	dsInstalled(t, root, "goodun", "goodun", "test.sh")

	require.NoError(t, plugin.NewManager().Uninstall(context.Background(), "goodun"))

	assert.NoDirExists(t, filepath.Join(root, "goodun"))
}

func TestFunc_UninstallMissing(t *testing.T) {
	dsHome(t)

	require.NoError(t, plugin.NewManager().Uninstall(context.Background(), "ghost"))
}

func TestFunc_StartNormal(t *testing.T) {
	_, root := dsHome(t)
	marker := filepath.Join(t.TempDir(), "marker")
	installed := dsInstalled(t, root, "goodrun", "goodrun", "run.sh")
	require.NoError(t, os.WriteFile(filepath.Join(installed, "run.sh"),
		[]byte("#!/bin/sh\ntouch \""+marker+"\"\n"), 0o755))

	w, err := plugin.NewManager().Start(context.Background(), "goodrun", dsOpts())
	require.NoError(t, err)
	require.NoError(t, w())

	assert.FileExists(t, marker)
}

func TestFunc_RepairNormal(t *testing.T) {
	_, root := dsHome(t)
	d := filepath.Join(root, "goodrepair")
	require.NoError(t, os.MkdirAll(d, 0o755))
	meta := "name: \"goodrepair\"\nrepository: testsrc\nversion: \"0.1.0\"\nusage: old summary\ndescription: test\n"
	require.NoError(t, os.WriteFile(filepath.Join(d, "plugin.yaml"), []byte(meta), 0o644))

	require.NoError(t, plugin.NewManager().Repair(context.Background()))

	b, err := os.ReadFile(filepath.Join(d, "plugin.yaml"))
	require.NoError(t, err)
	assert.Contains(t, string(b), "summary: old summary")
	assert.NotContains(t, string(b), "usage: old summary")
}

func TestFunc_RepairMissingRoot(t *testing.T) {
	t.Setenv("XDG_DATA_HOME", t.TempDir())

	require.NoError(t, plugin.NewManager().Repair(context.Background()))
}

func TestFunc_UpdateCachesIndex(t *testing.T) {
	_, root := dsHome(t)
	indexDir := t.TempDir()
	index := "version: 1\nplugins:\n  - name: \"goodcache\"\n    version: \"1.0.0\"\n" +
		"    maintainer: test\n    summary: test\n    repository: https://example.invalid/good\n    output: false\n"
	indexPath := filepath.Join(indexDir, "index.yaml")
	require.NoError(t, os.WriteFile(indexPath, []byte(index), 0o644))

	m := plugin.NewManager(plugin.WithIndexURL("file://" + indexPath))
	require.NoError(t, m.Update(context.Background(), plugin.Options{}))

	assert.FileExists(t, filepath.Join(root, "index.yaml"))
	assert.FileExists(t, filepath.Join(root, "goodcache.index", "index.json"))
}

func TestFunc_UpdateUnparsableIndex(t *testing.T) {
	_, root := dsHome(t)
	indexDir := t.TempDir()
	indexPath := filepath.Join(indexDir, "index.yaml")
	require.NoError(t, os.WriteFile(indexPath, []byte("this is not yaml"), 0o644))

	m := plugin.NewManager(plugin.WithIndexURL("file://" + indexPath))
	require.NoError(t, m.Update(context.Background(), plugin.Options{}))

	b, err := os.ReadFile(filepath.Join(root, "index.yaml"))
	require.NoError(t, err)
	assert.True(t, strings.Contains(string(b), "this is not yaml"))
}
