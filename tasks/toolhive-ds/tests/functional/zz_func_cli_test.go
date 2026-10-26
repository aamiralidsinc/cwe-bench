// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package app

import (
	"context"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/stacklok/toolhive/pkg/runner"
)

// An explicit opt-out is honoured, and a saved definition keeps it.

func TestFunc_CLIRunExplicitOptOut(t *testing.T) {
	flag := "false"
	cfg, _ := zzCLIConfig(t, &flag)
	require.NotNil(t, cfg)
	require.False(t, cfg.IsolateNetwork, "an explicit opt-out must be honoured")
}

func TestFunc_CLIRunExplicitOptIn(t *testing.T) {
	flag := "true"
	cfg, _ := zzCLIConfig(t, &flag)
	require.NotNil(t, cfg)
	require.True(t, cfg.IsolateNetwork)
}

// A saved definition that explicitly disables isolation must keep that
// choice when the definition is started again, including after it has been
// exported and read back.
func TestFunc_SavedDefinitionKeepsOptOut(t *testing.T) {
	zzInstallRuntime()
	t.Setenv("TOOLHIVE_RUNTIME", "zz-app-runtime")

	name := "zzfun-roundtrip"
	path := zzSaveExported(t, name, false)

	prev := runFlags
	runFlags = RunFlags{FromConfig: path, Name: name, Foreground: false}
	t.Cleanup(func() { runFlags = prev })
	_ = runFromConfigFile(context.Background())

	saved, err := runner.LoadState(context.Background(), name)
	require.NoError(t, err)
	require.False(t, saved.IsolateNetwork, "the recorded opt-out must be kept")
}

// An exported isolated definition still records the setting and starts isolated.
func TestFunc_SavedIsolatedDefinitionStaysIsolated(t *testing.T) {
	zzInstallRuntime()
	t.Setenv("TOOLHIVE_RUNTIME", "zz-app-runtime")

	name := "zzfun-roundtrip-iso"
	path := zzSaveExported(t, name, true)

	prev := runFlags
	runFlags = RunFlags{FromConfig: path, Name: name, Foreground: false}
	t.Cleanup(func() { runFlags = prev })
	_ = runFromConfigFile(context.Background())

	saved, err := runner.LoadState(context.Background(), name)
	require.NoError(t, err)
	require.True(t, saved.IsolateNetwork)
}
