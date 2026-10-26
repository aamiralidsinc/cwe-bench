// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package app

import (
	"context"
	"sync"
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"

	"github.com/stacklok/toolhive/pkg/config"
	rt "github.com/stacklok/toolhive/pkg/container/runtime"
	runtimemocks "github.com/stacklok/toolhive/pkg/container/runtime/mocks"
	"github.com/stacklok/toolhive/pkg/runner"
)

// zzReporter keeps the shared mock runtime quiet: the config builders ask for a
// runtime but never call a method on it.
type zzReporter struct{}

func (zzReporter) Errorf(string, ...interface{}) {}
func (zzReporter) Fatalf(string, ...interface{}) {}

var zzRuntimeOnce sync.Once

// zzInstallRuntime registers a container runtime the product code can pick up
// through TOOLHIVE_RUNTIME, so no Docker daemon is needed.
func zzInstallRuntime() {
	zzRuntimeOnce.Do(func() {
		fake := runtimemocks.NewMockRuntime(gomock.NewController(zzReporter{}))
		rt.RegisterRuntime(&rt.Info{
			Name:        "zz-app-runtime",
			Priority:    950,
			Initializer: func(context.Context) (rt.Runtime, error) { return fake, nil },
			AutoDetector: func() bool {
				return true
			},
		})
	})
}

// zzCLIConfig builds the run configuration the run command would build.
// flag is the raw value of the isolation option, or nil when the user did not
// pass one.
func zzCLIConfig(t *testing.T, flag *string) (*runner.RunConfig, *RunFlags) {
	t.Helper()
	ctrl := gomock.NewController(t)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	rf := &RunFlags{
		Transport:         "sse",
		ProxyMode:         "sse",
		Host:              "localhost",
		PermissionProfile: "none",
		Name:              "zz-cli-workload",
	}
	cmd := &cobra.Command{}
	AddRunFlags(cmd, rf)
	if flag != nil {
		require.NoError(t, cmd.ParseFlags([]string{"--isolate-network=" + *flag}))
	}

	cfg, err := buildRunnerConfig(context.Background(), rf, nil, false, "localhost", rtMock,
		"example/mcp:1.0.0", nil, map[string]string{}, &runner.DetachedEnvVarValidator{},
		nil, nil, config.NewDefaultProvider().GetConfig())
	require.NoError(t, err)
	return cfg, rf
}

// zzSaveExported writes a config to the state store and exports it through the
// real export command, returning the exported file path.
func zzSaveExported(t *testing.T, name string, isolate bool) string {
	t.Helper()
	ctx := context.Background()
	cfg := &runner.RunConfig{
		Name:           name,
		ContainerName:  name,
		BaseName:       name,
		Image:          "example/mcp:1.0.0",
		Transport:      "stdio",
		Host:           "127.0.0.1",
		IsolateNetwork: isolate,
	}
	require.NoError(t, cfg.SaveState(ctx))

	path := t.TempDir() + "/" + name + ".json"
	cmd := &cobra.Command{}
	cmd.SetContext(ctx)
	prev := exportFormat
	exportFormat = "json"
	t.Cleanup(func() { exportFormat = prev })
	require.NoError(t, exportCmdFunc(cmd, []string{name, path}))
	return path
}
