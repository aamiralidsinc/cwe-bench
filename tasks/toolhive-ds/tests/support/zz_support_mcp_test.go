// SPDX-FileCopyrightText: Copyright 2025 Stacklok, Inc.
// SPDX-License-Identifier: Apache-2.0

package server

import (
	"context"
	"sync"

	"go.uber.org/mock/gomock"

	rt "github.com/stacklok/toolhive/pkg/container/runtime"
	runtimemocks "github.com/stacklok/toolhive/pkg/container/runtime/mocks"
)

// zzReporter keeps the shared mock runtime quiet: the config builder asks the
// runtime factory for a runtime but never calls a method on it.
type zzReporter struct{}

func (zzReporter) Errorf(string, ...interface{}) {}
func (zzReporter) Fatalf(string, ...interface{}) {}

var zzRuntimeOnce sync.Once

// zzInstallRuntime registers a container runtime the config builder can pick
// up through TOOLHIVE_RUNTIME, so no Docker daemon is needed.
func zzInstallRuntime() {
	zzRuntimeOnce.Do(func() {
		fake := runtimemocks.NewMockRuntime(gomock.NewController(zzReporter{}))
		rt.RegisterRuntime(&rt.Info{
			Name:        "zz-task-runtime",
			Priority:    950,
			Initializer: func(context.Context) (rt.Runtime, error) { return fake, nil },
			AutoDetector: func() bool {
				return true
			},
		})
	})
}
