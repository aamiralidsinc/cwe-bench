// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package v1

import (
	"context"
	"net/http"
	"net/http/httptest"

	regtypes "github.com/stacklok/toolhive-core/registry/types"

	apierrors "github.com/stacklok/toolhive/pkg/api/errors"
	"github.com/stacklok/toolhive/pkg/config"
	"github.com/stacklok/toolhive/pkg/container/runtime"
	"github.com/stacklok/toolhive/pkg/container/templates"
	"github.com/stacklok/toolhive/pkg/groups"
	"github.com/stacklok/toolhive/pkg/runner/retriever"
	"github.com/stacklok/toolhive/pkg/workloads"
)

// zzRetriever resolves any image reference to a container server without
// touching a registry, a network or a container runtime.
func zzRetriever(_ context.Context, serverOrImage string, _ string, _ string, _ string,
	_ *templates.RuntimeConfig,
) (string, regtypes.ServerMetadata, error) {
	return serverOrImage, &regtypes.ImageMetadata{Image: serverOrImage}, nil
}

// zzRoutes builds the real workload routes with every external dependency
// replaced by a stub.
func zzRoutes(wm workloads.Manager, rt runtime.Runtime, gm groups.Manager) *WorkloadRoutes {
	return &WorkloadRoutes{
		workloadManager:  wm,
		containerRuntime: rt,
		groupManager:     gm,
		debugMode:        false,
		workloadService: &WorkloadService{
			groupManager:      gm,
			workloadManager:   wm,
			containerRuntime:  rt,
			imageRetriever:    zzRetriever,
			imagePuller:       func(context.Context, string) error { return nil },
			configProvider:    config.NewDefaultProvider(),
			imageVerification: retriever.VerifyImageWarn,
		},
	}
}

// zzDo runs one handler the same way the router does.
func zzDo(handler func(http.ResponseWriter, *http.Request) error, req *http.Request) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	apierrors.ErrorHandler(handler).ServeHTTP(w, req)
	return w
}
