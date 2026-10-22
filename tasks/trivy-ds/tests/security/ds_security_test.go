//go:build unix

// Security tests: no plugin name, from any source, may cause a file or
// directory outside the plugin directory to be created, removed, written, read
// or executed. Each test drives a real plugin management operation and asserts
// only that the out-of-directory side effect did not happen.

package plugin_test

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/aquasecurity/trivy/pkg/plugin"
)

func TestSec_InstallEscapingName(t *testing.T) {
	home, _ := dsHome(t)
	escaped := filepath.Join(home, ".trivy", "escaped_plugin")
	require.NoError(t, os.MkdirAll(escaped, 0o755))
	sentinel := filepath.Join(escaped, "keep.txt")
	require.NoError(t, os.WriteFile(sentinel, []byte("keep"), 0o644))

	_, _ = plugin.NewManager().Install(context.Background(), dsSource(t, "../escaped_plugin"), dsOpts())

	assert.FileExists(t, sentinel, "install removed a directory outside the plugin directory")
	assert.NoFileExists(t, filepath.Join(escaped, "plugin.yaml"), "install wrote metadata outside the plugin directory")
}

func TestSec_InstallCleanEscape(t *testing.T) {
	home, _ := dsHome(t)

	_, _ = plugin.NewManager().Install(context.Background(), dsSource(t, "missing/../../escaped_clean"), dsOpts())

	assert.NoDirExists(t, filepath.Join(home, ".trivy", "escaped_clean"),
		"install created a directory outside the plugin directory")
}

func TestSec_InstallPrefixSibling(t *testing.T) {
	home, _ := dsHome(t)

	_, _ = plugin.NewManager().Install(context.Background(), dsSource(t, "../plugins_evil"), dsOpts())

	assert.NoDirExists(t, filepath.Join(home, ".trivy", "plugins_evil"),
		"install created a directory next to the plugin directory")
}

func TestSec_InstallSymlinkEscape(t *testing.T) {
	_, root := dsHome(t)
	outside := t.TempDir()
	require.NoError(t, os.MkdirAll(filepath.Join(outside, "sub"), 0o755))
	sentinel := filepath.Join(outside, "sub", "keep.txt")
	require.NoError(t, os.WriteFile(sentinel, []byte("keep"), 0o644))
	require.NoError(t, os.Symlink(outside, filepath.Join(root, "link")))

	_, _ = plugin.NewManager().Install(context.Background(), dsSource(t, "link/sub"), dsOpts())

	assert.FileExists(t, sentinel, "install removed a directory reached through a link")
	assert.NoFileExists(t, filepath.Join(outside, "sub", "plugin.yaml"),
		"install wrote metadata through a link to outside the plugin directory")
}

func TestSec_UninstallEscapingName(t *testing.T) {
	home, _ := dsHome(t)
	secret := filepath.Join(home, ".trivy", "secret")
	require.NoError(t, os.MkdirAll(secret, 0o755))
	sentinel := filepath.Join(secret, "keep.txt")
	require.NoError(t, os.WriteFile(sentinel, []byte("keep"), 0o644))

	_ = plugin.NewManager().Uninstall(context.Background(), "../secret")

	assert.FileExists(t, sentinel, "uninstall removed a directory outside the plugin directory")
}

func TestSec_InformationEscapingName(t *testing.T) {
	home, _ := dsHome(t)
	outside := filepath.Join(home, "outside")
	require.NoError(t, os.MkdirAll(outside, 0o755))
	meta := "name: \"outside_plugin\"\nrepository: testsrc\nversion: \"9.9.9\"\n" +
		"summary: SPECIMEN-SUMMARY\ndescription: SPECIMEN-DESCRIPTION\n"
	require.NoError(t, os.WriteFile(filepath.Join(outside, "plugin.yaml"), []byte(meta), 0o644))

	var got bytes.Buffer
	m := plugin.NewManager(plugin.WithWriter(&got))
	_ = m.Information("../../outside")

	assert.NotContains(t, got.String(), "SPECIMEN-SUMMARY",
		"information was read from outside the plugin directory")
	assert.NotContains(t, got.String(), "SPECIMEN-DESCRIPTION",
		"information was read from outside the plugin directory")
}

func TestSec_UninstallParentName(t *testing.T) {
	home, _ := dsHome(t)
	sentinel := filepath.Join(home, ".trivy", "keep.txt")
	require.NoError(t, os.WriteFile(sentinel, []byte("keep"), 0o644))

	_ = plugin.NewManager().Uninstall(context.Background(), "..")

	assert.FileExists(t, sentinel, "uninstall removed the directory above the plugin directory")
}

func TestSec_StoredNameExecution(t *testing.T) {
	home, root := dsHome(t)
	marker := filepath.Join(t.TempDir(), "marker")
	outside := filepath.Join(home, "escaped_exec")
	require.NoError(t, os.MkdirAll(outside, 0o755))
	require.NoError(t, os.WriteFile(filepath.Join(outside, "run.sh"),
		[]byte("#!/bin/sh\ntouch \""+marker+"\"\n"), 0o755))
	dsInstalled(t, root, "legit", "../../escaped_exec", "run.sh")

	w, err := plugin.NewManager().Start(context.Background(), "legit", dsOpts())
	if err == nil {
		_ = w()
	}

	assert.NoFileExists(t, marker, "a plugin recorded outside the plugin directory was executed")
}

func TestSec_RepairStoredName(t *testing.T) {
	home, root := dsHome(t)
	installed := dsInstalled(t, root, "legit", "../../escaped_repair", "test.sh")
	require.NoError(t, os.WriteFile(filepath.Join(installed, "test.sh"), []byte("#!/bin/sh\nexit 0\n"), 0o755))

	_ = plugin.NewManager().Repair(context.Background())

	assert.NoDirExists(t, filepath.Join(home, "escaped_repair"),
		"repair created a directory outside the plugin directory")
	assert.NoFileExists(t, filepath.Join(home, "escaped_repair", "plugin.yaml"),
		"repair wrote metadata outside the plugin directory")
}

func TestSec_IndexEntryName(t *testing.T) {
	home, _ := dsHome(t)
	indexDir := t.TempDir()
	index := "version: 1\nplugins:\n  - name: \"../../escaped_index\"\n    version: \"1.0.0\"\n" +
		"    maintainer: test\n    summary: test\n    repository: https://example.invalid/evil\n    output: false\n"
	indexPath := filepath.Join(indexDir, "index.yaml")
	require.NoError(t, os.WriteFile(indexPath, []byte(index), 0o644))

	m := plugin.NewManager(plugin.WithIndexURL("file://" + indexPath))
	_ = m.Update(context.Background(), plugin.Options{})

	assert.NoDirExists(t, filepath.Join(home, "escaped_index.index"),
		"updating the index created a directory outside the plugin directory")
}
