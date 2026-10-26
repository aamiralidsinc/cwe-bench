// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package server

import (
	"context"
	"testing"

	"github.com/stretchr/testify/require"
)

// A server started through the run-server tool must be network-isolated by
// default. The tool arguments below do not mention isolation at all.

func TestSec_RunServerToolDefaultsToIsolation(t *testing.T) {
	zzInstallRuntime()
	t.Setenv("TOOLHIVE_RUNTIME", "zz-task-runtime")

	cfg, err := buildServerConfig(context.Background(),
		&runServerArgs{Server: "example/mcp:1.0.0", Name: "zzsec-mcp", Host: "127.0.0.1"},
		"example/mcp:1.0.0", nil)
	require.NoError(t, err)
	require.NotNil(t, cfg)
	require.True(t, cfg.IsolateNetwork,
		"a server started without mentioning isolation must be isolated")
}
