//go:build unix

// Security tests: no plugin name, from any source, may cause a file to be
// written, deleted or created outside the managed plugin directory. Each test
// drives a real plugin management operation and asserts that nothing outside
// the plugin root was touched. They fail on the vulnerable code and pass on a
// correct fix. They never assert a particular error, only the absence of any
// out-of-root side effect.

package plugin_test

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/aquasecurity/trivy/pkg/clock"
	"github.com/aquasecurity/trivy/pkg/plugin"
)


// A plugin installed from a source whose metadata name escapes the plugin root
// must not create any directory outside that root.
func TestSec_InstallEscapingName(t *testing.T) {
	home, _ := vHome(t)
	src := filepath.Join(t.TempDir(), "src")
	writeSrcPlugin(t, src, "../escaped_plugin")
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_, _ = plugin.NewManager().Install(ctx, src, instOpts())

	escaped := filepath.Join(home, ".trivy", "escaped_plugin")
	assert.NoDirExists(t, escaped, "install created a plugin directory outside the plugin root")
}

// Uninstalling with a name that escapes the plugin root must not delete
// anything outside that root.
func TestSec_UninstallEscapingName(t *testing.T) {
	home, _ := vHome(t)
	sentinelDir := filepath.Join(home, ".trivy", "secret")
	require.NoError(t, os.MkdirAll(sentinelDir, 0o755))
	sentinel := filepath.Join(sentinelDir, "keep.txt")
	require.NoError(t, os.WriteFile(sentinel, []byte("keep"), 0o600))
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_ = plugin.NewManager().Uninstall(ctx, "../secret")

	assert.FileExists(t, sentinel, "uninstall removed a path outside the plugin root")
}

// An installed plugin whose stored metadata name escapes the plugin root must
// not cause a later management operation to write outside that root.
func TestSec_RefreshStoredName(t *testing.T) {
	home, root := vHome(t)
	setupInstalled(t, root, "legit", "../../escaped_refresh")
	require.NoError(t, os.MkdirAll(filepath.Join(home, "escaped_refresh"), 0o755))
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_ = plugin.NewManager().Refresh(ctx, "legit")

	marker := filepath.Join(home, "escaped_refresh", ".refreshed")
	assert.NoFileExists(t, marker, "a management operation wrote outside the plugin root via a stored name")
}

// Reserving a cache for a plugin named so that it escapes the plugin root must
// not create anything outside that root.
func TestSec_PrefetchEscapingName(t *testing.T) {
	home, _ := vHome(t)
	ctx := clock.With(t.Context(), time.Date(2021, 8, 25, 12, 20, 30, 5, time.UTC))

	_ = plugin.NewManager().Prefetch(ctx, "../../escaped_prefetch")

	escaped := filepath.Join(home, "escaped_prefetch.cache")
	assert.NoDirExists(t, escaped, "a cache directory was created outside the plugin root")
}
