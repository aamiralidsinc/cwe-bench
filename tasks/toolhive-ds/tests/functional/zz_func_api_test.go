// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package v1

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"

	runtimemocks "github.com/stacklok/toolhive/pkg/container/runtime/mocks"
	"github.com/stacklok/toolhive/pkg/core"
	groupsmocks "github.com/stacklok/toolhive/pkg/groups/mocks"
	"github.com/stacklok/toolhive/pkg/runner"
	"github.com/stacklok/toolhive/pkg/workloads"
	workloadsmocks "github.com/stacklok/toolhive/pkg/workloads/mocks"
)

// An explicit opt-out is honoured, and an explicit opt-in stays isolated.

func TestFunc_APICreateExplicitOptOut(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().DoesWorkloadExist(gomock.Any(), "zzfun-optout").Return(false, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var started *runner.RunConfig
	wm.EXPECT().RunWorkloadDetached(gomock.Any(), gomock.Any()).
		DoAndReturn(func(_ context.Context, cfg *runner.RunConfig) error {
			started = cfg
			return nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"name":"zzfun-optout","image":"example/mcp:1.0.0","transport":"streamable-http",` +
		`"network_isolation":false}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.createWorkload, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.False(t, started.IsolateNetwork, "an explicit opt-out must be honoured")
}

func TestFunc_APICreateExplicitOptIn(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().DoesWorkloadExist(gomock.Any(), "zzfun-optin").Return(false, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var started *runner.RunConfig
	wm.EXPECT().RunWorkloadDetached(gomock.Any(), gomock.Any()).
		DoAndReturn(func(_ context.Context, cfg *runner.RunConfig) error {
			started = cfg
			return nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"name":"zzfun-optin","image":"example/mcp:1.0.0","transport":"streamable-http",` +
		`"network_isolation":true}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.createWorkload, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.True(t, started.IsolateNetwork)
}

func TestFunc_APIUpdateExplicitOptOut(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().GetWorkload(gomock.Any(), "zzfun-updoptout").
		Return(core.Workload{Name: "zzfun-updoptout", Port: 8080}, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var updated *runner.RunConfig
	wm.EXPECT().UpdateWorkload(gomock.Any(), "zzfun-updoptout", gomock.Any()).
		DoAndReturn(func(_ context.Context, _ string, cfg *runner.RunConfig) (workloads.CompletionFunc, error) {
			updated = cfg
			return func() error { return nil }, nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"image":"example/mcp:1.0.0","transport":"streamable-http","network_isolation":false}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads/zzfun-updoptout/edit", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("name", "zzfun-updoptout")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	w := zzDo(routes.updateWorkload, req)

	require.Equal(t, http.StatusOK, w.Code, w.Body.String())
	require.NotNil(t, updated)
	require.False(t, updated.IsolateNetwork, "an explicit opt-out on edit must be honoured")
}

func TestFunc_APIImportExplicitOptOut(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	var started *runner.RunConfig
	wm.EXPECT().RunWorkloadDetached(gomock.Any(), gomock.Any()).
		DoAndReturn(func(_ context.Context, cfg *runner.RunConfig) error {
			started = cfg
			return nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"definitions":[{"name":"zzfun-impoptout","container_name":"zzfun-impoptout",` +
		`"base_name":"zzfun-impoptout","image":"example/mcp:1.0.0","transport":"stdio",` +
		`"isolate_network":false}]}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads/import", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.importWorkloads, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.False(t, started.IsolateNetwork, "an explicit opt-out in a definition must be honoured")
}

// A defaulted create keeps every other field the caller supplied.
func TestFunc_APICreateKeepsOtherFields(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().DoesWorkloadExist(gomock.Any(), "zzfun-fields").Return(false, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var started *runner.RunConfig
	wm.EXPECT().RunWorkloadDetached(gomock.Any(), gomock.Any()).
		DoAndReturn(func(_ context.Context, cfg *runner.RunConfig) error {
			started = cfg
			return nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"name":"zzfun-fields","image":"example/mcp:1.0.0","transport":"streamable-http",` +
		`"env_vars":{"GREETING":"hello"},"target_port":8123}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.createWorkload, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.Equal(t, "zzfun-fields", started.Name)
	require.Equal(t, "example/mcp:1.0.0", started.Image)
	require.Equal(t, "hello", started.EnvVars["GREETING"])
	require.Equal(t, 8123, started.TargetPort)
}
