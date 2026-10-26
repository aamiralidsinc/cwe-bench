//go:build test_unit

// Functional tests for the local deployment backend: legitimate project writes keep
// working after the authorization checks are added, including writes made with the
// deployment's configured trusted role and deployments without an authorization
// service.

package local

import (
	"context"
	"testing"
	"time"

	"github.com/nuclio/nuclio/pkg/auth/nop"
	"github.com/nuclio/nuclio/pkg/platform"
	"github.com/nuclio/nuclio/pkg/platform/abstract"
	abstractproject "github.com/nuclio/nuclio/pkg/platform/abstract/project"
	mockplatform "github.com/nuclio/nuclio/pkg/platform/mock"
	"github.com/nuclio/nuclio/pkg/platformconfig"

	"github.com/nuclio/logger"
	"github.com/nuclio/opa-client"
	nucliozap "github.com/nuclio/zap"
	"github.com/stretchr/testify/mock"
)

const funLocalNamespace = "fun-namespace"

const funLocalTrustedRole = "fun-local-trusted-role-value"

type funLocalWrites struct {
	creates int
	updates int
	deletes int
}

func (w *funLocalWrites) Initialize() error { return nil }

func (w *funLocalWrites) Create(_ context.Context, _ *platform.CreateProjectOptions) (platform.Project, error) {
	w.creates++
	return nil, nil
}

func (w *funLocalWrites) Update(_ context.Context, _ *platform.UpdateProjectOptions) (platform.Project, error) {
	w.updates++
	return nil, nil
}

func (w *funLocalWrites) Delete(_ context.Context, _ *platform.DeleteProjectOptions) error {
	w.deletes++
	return nil
}

func (w *funLocalWrites) Get(_ context.Context, _ *platform.GetProjectsOptions) ([]platform.Project, error) {
	return nil, nil
}

var _ abstractproject.Client = &funLocalWrites{}

type funAllowAllOpa struct{}

func (f *funAllowAllOpa) QueryPermissions(_ context.Context,
	_ string,
	_ opaclient.Action,
	_ *opaclient.PermissionOptions) (bool, error) {
	return true, nil
}

func (f *funAllowAllOpa) QueryPermissionsMultiResources(_ context.Context,
	resources []string,
	_ opaclient.Action,
	_ *opaclient.PermissionOptions) ([]bool, error) {
	allowed := make([]bool, len(resources))
	for i := range allowed {
		allowed[i] = true
	}
	return allowed, nil
}

type funLocalRig struct {
	platform *Platform
	writes   *funLocalWrites
	logger   logger.Logger
}

func newFunLocalRig(t *testing.T) *funLocalRig {
	logger, err := nucliozap.NewNuclioZapTest("fun")
	if err != nil {
		t.Fatalf("failed to create logger: %v", err)
	}

	config := &platformconfig.Config{}
	if err := config.EnrichPlatformConfig(); err != nil {
		t.Fatalf("failed to enrich platform config: %v", err)
	}

	mockedPlatform := &mockplatform.Platform{}
	mockedPlatform.On("GetProjects", mock.Anything, mock.Anything).
		Return([]platform.Project{&platform.AbstractProject{}}, nil).Maybe()
	mockedPlatform.On("GetFunctions", mock.Anything, mock.Anything).
		Return([]platform.Function{}, nil).Maybe()
	mockedPlatform.On("GetAPIGateways", mock.Anything, mock.Anything).
		Return([]platform.APIGateway{}, nil).Maybe()

	abstractPlatform, err := abstract.NewPlatform(logger, mockedPlatform, config, "")
	if err != nil {
		t.Fatalf("failed to create abstract platform: %v", err)
	}
	abstractPlatform.OpaClient = &funAllowAllOpa{}

	writes := &funLocalWrites{}
	return &funLocalRig{
		platform: &Platform{Platform: abstractPlatform, projectsClient: writes},
		writes:   writes,
		logger:   logger,
	}
}

func funLocalProjectConfig(name string) *platform.ProjectConfig {
	return &platform.ProjectConfig{
		Meta: platform.ProjectMeta{Name: name, Namespace: funLocalNamespace},
		Spec: platform.ProjectSpec{Description: "some description"},
	}
}

func TestFuncLocalAllowedWrites(t *testing.T) {
	rig := newFunLocalRig(t)
	ctx := context.Background()

	if err := rig.platform.CreateProject(ctx, &platform.CreateProjectOptions{
		AuthSession:       &nop.Session{},
		ProjectConfig:     funLocalProjectConfig("my-project"),
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed create failed: %v", err)
	}
	if rig.writes.creates != 1 {
		t.Fatalf("create did not reach the project storage")
	}

	if err := rig.platform.UpdateProject(ctx, &platform.UpdateProjectOptions{
		ProjectConfig:     *funLocalProjectConfig("my-project"),
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed update failed: %v", err)
	}
	if rig.writes.updates != 1 {
		t.Fatalf("update did not reach the project storage")
	}

	if err := rig.platform.DeleteProject(ctx, &platform.DeleteProjectOptions{
		AuthSession:       &nop.Session{},
		Meta:              platform.ProjectMeta{Name: "my-project", Namespace: funLocalNamespace},
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed delete failed: %v", err)
	}
	if rig.writes.deletes != 1 {
		t.Fatalf("delete did not reach the project storage")
	}
}

func TestFuncLocalTrustedRoleDelete(t *testing.T) {
	rig := newFunLocalRig(t)
	rig.platform.OpaClient = opaclient.NewHTTPClient(rig.logger,
		"http://127.0.0.1:1",
		"/v1/data/authz/allow",
		"/v1/data/authz/filter_allowed",
		time.Second,
		false,
		funLocalTrustedRole,
		false)

	if err := rig.platform.DeleteProject(context.Background(), &platform.DeleteProjectOptions{
		AuthSession: &nop.Session{},
		Meta:        platform.ProjectMeta{Name: "my-project", Namespace: funLocalNamespace},
		PermissionOptions: opaclient.PermissionOptions{
			OverrideHeaderValue: funLocalTrustedRole,
		},
	}); err != nil {
		t.Fatalf("delete with the trusted role failed: %v", err)
	}
	if rig.writes.deletes != 1 {
		t.Fatalf("delete with the trusted role did not reach the project storage")
	}
}

func TestFuncLocalNoPolicyService(t *testing.T) {
	rig := newFunLocalRig(t)
	rig.platform.OpaClient = opaclient.NewNopClient(rig.logger, false)

	if err := rig.platform.CreateProject(context.Background(), &platform.CreateProjectOptions{
		AuthSession:   &nop.Session{},
		ProjectConfig: funLocalProjectConfig("my-project"),
	}); err != nil {
		t.Fatalf("create without an authorization service failed: %v", err)
	}
	if rig.writes.creates != 1 {
		t.Fatalf("create without an authorization service did not reach the project storage")
	}
}
