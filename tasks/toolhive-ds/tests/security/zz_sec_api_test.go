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

// A server started through the workload API must be network-isolated by
// default. The start request below does not mention isolation at all.

func TestSec_APICreateOmittedIsolation(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().DoesWorkloadExist(gomock.Any(), "zzsec-create").Return(false, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var started *runner.RunConfig
	wm.EXPECT().RunWorkloadDetached(gomock.Any(), gomock.Any()).
		DoAndReturn(func(_ context.Context, cfg *runner.RunConfig) error {
			started = cfg
			return nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"name":"zzsec-create","image":"example/mcp:1.0.0","transport":"streamable-http"}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.createWorkload, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.True(t, started.IsolateNetwork,
		"a server started without mentioning isolation must be isolated")
}

func TestSec_APIUpdateOmittedIsolation(t *testing.T) {
	ctrl := gomock.NewController(t)
	wm := workloadsmocks.NewMockManager(ctrl)
	gm := groupsmocks.NewMockManager(ctrl)
	rtMock := runtimemocks.NewMockRuntime(ctrl)

	wm.EXPECT().GetWorkload(gomock.Any(), "zzsec-update").
		Return(core.Workload{Name: "zzsec-update", Port: 8080}, nil)
	gm.EXPECT().Exists(gomock.Any(), "default").Return(true, nil)
	var updated *runner.RunConfig
	wm.EXPECT().UpdateWorkload(gomock.Any(), "zzsec-update", gomock.Any()).
		DoAndReturn(func(_ context.Context, _ string, cfg *runner.RunConfig) (workloads.CompletionFunc, error) {
			updated = cfg
			return func() error { return nil }, nil
		})

	routes := zzRoutes(wm, rtMock, gm)
	body := `{"image":"example/mcp:1.0.0","transport":"streamable-http"}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads/zzsec-update/edit", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("name", "zzsec-update")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	w := zzDo(routes.updateWorkload, req)

	require.Equal(t, http.StatusOK, w.Code, w.Body.String())
	require.NotNil(t, updated)
	require.True(t, updated.IsolateNetwork,
		"an edit that does not mention isolation must keep the server isolated")
}

func TestSec_APIImportOmittedIsolation(t *testing.T) {
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
	body := `{"definitions":[{"name":"zzsec-import","container_name":"zzsec-import",` +
		`"base_name":"zzsec-import","image":"example/mcp:1.0.0","transport":"stdio"}]}`
	req := httptest.NewRequest(http.MethodPost, "/api/v1beta/workloads/import", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := zzDo(routes.importWorkloads, req)

	require.Equal(t, http.StatusCreated, w.Code, w.Body.String())
	require.NotNil(t, started)
	require.True(t, started.IsolateNetwork,
		"a definition that does not mention isolation must start isolated")
}
