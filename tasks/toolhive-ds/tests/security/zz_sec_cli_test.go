// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package app

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/stacklok/toolhive/pkg/runner"
)

// A server started by the run command, and one started from a saved
// definition, must be network-isolated when nothing says otherwise.

func TestSec_CLIRunDefaultsToIsolation(t *testing.T) {
	cfg, _ := zzCLIConfig(t, nil)
	require.NotNil(t, cfg)
	require.True(t, cfg.IsolateNetwork,
		"a server started without mentioning isolation must be isolated")
}

func TestSec_SavedDefinitionDefaultsToIsolation(t *testing.T) {
	zzInstallRuntime()
	t.Setenv("TOOLHIVE_RUNTIME", "zz-app-runtime")

	name := "zzsec-saved"
	path := filepath.Join(t.TempDir(), "definition.json")
	// The definition says nothing about isolation.
	body := `{"name":"` + name + `","container_name":"` + name + `","base_name":"` + name + `",` +
		`"image":"example/mcp:1.0.0","transport":"stdio"}`
	require.NoError(t, os.WriteFile(path, []byte(body), 0o600))

	prev := runFlags
	runFlags = RunFlags{FromConfig: path, Name: name, Foreground: false}
	t.Cleanup(func() { runFlags = prev })

	// The detached spawn is irrelevant here: the definition is persisted before
	// the workload is started, and that persisted definition is what runs.
	_ = runFromConfigFile(context.Background())

	saved, err := runner.LoadState(context.Background(), name)
	require.NoError(t, err)
	require.True(t, saved.IsolateNetwork,
		"a definition that does not mention isolation must start isolated")
}
