//go:build unix

// Functional tests: every legitimate plugin management operation keeps working
// exactly as before. These must pass on both the vulnerable and the fixed code.

package plugin_test

import (
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/aquasecurity/trivy/pkg/clock"
	"github.com/aquasecurity/trivy/pkg/plugin"
)

// A plugin installed from a local path (a source containing a path separator)
// is installed under the plugin root.
func TestFunc_InstallLocal(t *testing.T) {
	_, root := vHome(t)
	src := filepath.Join(t.TempDir(), "goodplugin")
	writeSrcPlugin(t, src, "goodplugin")
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_, err := plugin.NewManager().Install(ctx, src, instOpts())
	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "goodplugin", "test.sh"))
	assert.FileExists(t, filepath.Join(root, "goodplugin", "plugin.yaml"))
}

// A source that wraps the plugin in a single top-level directory is unwrapped
// and installed under the plugin root.
func TestFunc_InstallNested(t *testing.T) {
	_, root := vHome(t)
	parent := filepath.Join(t.TempDir(), "parent")
	writeSrcPlugin(t, filepath.Join(parent, "inner"), "nestedplugin")
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_, err := plugin.NewManager().Install(ctx, parent, instOpts())
	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "nestedplugin", "test.sh"))
}

// Uninstalling an installed plugin removes its directory.
func TestFunc_UninstallExisting(t *testing.T) {
	_, root := vHome(t)
	setupInstalled(t, root, "goodun", "goodun")
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	err := plugin.NewManager().Uninstall(ctx, "goodun")
	require.NoError(t, err)
	assert.NoDirExists(t, filepath.Join(root, "goodun"))
}

// Uninstalling a plugin that is not installed is a no-op that returns no error.
func TestFunc_UninstallMissing(t *testing.T) {
	vHome(t)
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	err := plugin.NewManager().Uninstall(ctx, "ghost")
	require.NoError(t, err)
}

// Refreshing a normally installed plugin records its marker inside its own
// directory.
func TestFunc_RefreshNormal(t *testing.T) {
	_, root := vHome(t)
	setupInstalled(t, root, "goodref", "goodref")
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	err := plugin.NewManager().Refresh(ctx, "goodref")
	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "goodref", ".refreshed"))
}

// Reserving a cache for a normally named plugin creates it inside the plugin
// root.
func TestFunc_PrefetchNormal(t *testing.T) {
	_, root := vHome(t)
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	err := plugin.NewManager().Prefetch(ctx, "goodpf")
	require.NoError(t, err)
	assert.FileExists(t, filepath.Join(root, "goodpf.cache", "index.json"))
}
