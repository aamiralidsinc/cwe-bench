// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package upgrade

import (
	"context"
	"testing"
	"time"

	regtypes "github.com/stacklok/toolhive-core/registry/types"
	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"

	appconfig "github.com/stacklok/toolhive/pkg/config"
	configmocks "github.com/stacklok/toolhive/pkg/config/mocks"
	"github.com/stacklok/toolhive/pkg/container/templates"
	registrymocks "github.com/stacklok/toolhive/pkg/registry/mocks"
	"github.com/stacklok/toolhive/pkg/runner"
	"github.com/stacklok/toolhive/pkg/runner/retriever"
	transporttypes "github.com/stacklok/toolhive/pkg/transport/types"
	"github.com/stacklok/toolhive/pkg/workloads"
	workloadmocks "github.com/stacklok/toolhive/pkg/workloads/mocks"
)

// Changing a server's version must not change the isolation setting it was
// configured with, including an explicit opt-out.
func TestFunc_UpgradeKeepsExplicitOptOut(t *testing.T) {
	ctrl := gomock.NewController(t)
	manager := workloadmocks.NewMockManager(ctrl)
	provider := registrymocks.NewMockProvider(ctrl)
	configMock := configmocks.NewMockProvider(ctrl)

	checker, err := NewChecker(provider)
	require.NoError(t, err)
	applier, err := NewApplier(manager, checker, configMock)
	require.NoError(t, err)

	old := &runner.RunConfig{
		Name:               "wl",
		Image:              "ghcr.io/example/server:1.0.0",
		RegistryServerName: "zz-example-server",
		Group:              "default",
		Transport:          transporttypes.TransportTypeStdio,
		ProxyMode:          transporttypes.ProxyModeStreamableHTTP,
		Host:               "127.0.0.1",
		Port:               8080,
		IsolateNetwork:     false,
		EnvVars:            map[string]string{},
	}

	applier.loadStateFn = func(context.Context, string) (*runner.RunConfig, error) {
		return old, nil
	}
	candidate := &regtypes.ImageMetadata{Image: "ghcr.io/example/server:1.2.0"}
	candidate.Name = old.RegistryServerName
	applier.resolveFn = func(context.Context, string, string, string, string,
		*templates.RuntimeConfig,
	) (string, regtypes.ServerMetadata, error) {
		return candidate.Image, candidate, nil
	}
	applier.enforcePullFn = func(context.Context, *runner.RunConfig, regtypes.ServerMetadata,
		string, retriever.ImagePuller, time.Duration, bool,
	) error {
		return nil
	}

	provider.EXPECT().GetServer(old.RegistryServerName).Return(candidate, nil)
	configMock.EXPECT().GetConfig().
		Return(&appconfig.Config{RegistryApiUrl: "https://api.example", RegistryUrl: "https://reg.example"}).
		AnyTimes()

	var updated *runner.RunConfig
	manager.EXPECT().UpdateWorkload(gomock.Any(), "wl", gomock.Any()).
		DoAndReturn(func(_ context.Context, _ string, cfg *runner.RunConfig) (workloads.CompletionFunc, error) {
			updated = cfg
			return func() error { return nil }, nil
		})

	_, err = applier.Apply(context.Background(), "wl", ApplyOptions{
		EnvVarValidator: &runner.DetachedEnvVarValidator{},
	})
	require.NoError(t, err)
	require.NotNil(t, updated)
	require.Equal(t, "ghcr.io/example/server:1.2.0", updated.Image)
	require.False(t, updated.IsolateNetwork,
		"an explicit opt-out must survive a version change")
}
