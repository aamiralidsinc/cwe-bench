// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package runner

import (
	"context"
	"io"
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/stacklok/toolhive/pkg/state"
)

// An existing stored server keeps the isolation setting it was configured
// with. In particular, a stored definition written before the setting existed
// says nothing about isolation and must keep running without it; reading it
// must not silently rewrite the setting.
func TestFunc_StoredSettingIsNotRewritten(t *testing.T) {
	ctx := context.Background()
	name := "zzfun-oldstate"

	store, err := state.NewRunConfigStore(state.DefaultAppName)
	require.NoError(t, err)
	w, err := store.GetWriter(ctx, name)
	require.NoError(t, err)
	// An old definition: it never mentions isolation.
	_, err = io.WriteString(w, `{"name":"`+name+`","base_name":"`+name+`",`+
		`"container_name":"`+name+`","image":"example/mcp:1.0.0","transport":"stdio"}`)
	require.NoError(t, err)
	require.NoError(t, w.Close())

	cfg, err := LoadState(ctx, name)
	require.NoError(t, err)
	require.False(t, cfg.IsolateNetwork,
		"an existing setting must not be rewritten when a server is loaded")
}
