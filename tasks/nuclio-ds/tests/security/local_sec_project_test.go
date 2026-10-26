//go:build test_unit

// Security tests: every operation the product offers for writing a project must ask the
// deployment's authorization service about the project it is about to write and must
// refuse, with no side effect, when the caller is not allowed. These drive the real
// platform API of the local deployment backend.

package local

import (
	"context"
	"net/http"
	"testing"

	"github.com/nuclio/nuclio/pkg/auth/nop"
	"github.com/nuclio/nuclio/pkg/common"
	"github.com/nuclio/nuclio/pkg/platform"
	"github.com/nuclio/nuclio/pkg/platform/abstract"
	abstractproject "github.com/nuclio/nuclio/pkg/platform/abstract/project"
	mockplatform "github.com/nuclio/nuclio/pkg/platform/mock"
	"github.com/nuclio/nuclio/pkg/platformconfig"

	"github.com/nuclio/opa-client"
	nucliozap "github.com/nuclio/zap"
	"github.com/stretchr/testify/mock"
)

const secLocalNamespace = "sec-namespace"

type secLocalOpa struct {
	allow func(resource string, action opaclient.Action) bool
}

func (s *secLocalOpa) QueryPermissions(_ context.Context,
	resource string,
	action opaclient.Action,
	_ *opaclient.PermissionOptions) (bool, error) {
	return s.allow(resource, action), nil
}

func (s *secLocalOpa) QueryPermissionsMultiResources(_ context.Context,
	resources []string,
	action opaclient.Action,
	_ *opaclient.PermissionOptions) ([]bool, error) {
	allowed := make([]bool, len(resources))
	for i, resource := range resources {
		allowed[i] = s.allow(resource, action)
	}
	return allowed, nil
}

// secLocalWrites records project writes that reached the storage layer
type secLocalWrites struct {
	creates int
	updates int
	deletes int
}

func (w *secLocalWrites) Initialize() error { return nil }

func (w *secLocalWrites) Create(_ context.Context, _ *platform.CreateProjectOptions) (platform.Project, error) {
	w.creates++
	return nil, nil
}

func (w *secLocalWrites) Update(_ context.Context, _ *platform.UpdateProjectOptions) (platform.Project, error) {
	w.updates++
	return nil, nil
}

func (w *secLocalWrites) Delete(_ context.Context, _ *platform.DeleteProjectOptions) error {
	w.deletes++
	return nil
}

func (w *secLocalWrites) Get(_ context.Context, _ *platform.GetProjectsOptions) ([]platform.Project, error) {
	return nil, nil
}

var _ abstractproject.Client = &secLocalWrites{}

type secLocalRig struct {
	platform *Platform
	writes   *secLocalWrites
	opa      *secLocalOpa
}

func newSecLocalRig(t *testing.T) *secLocalRig {
	logger, err := nucliozap.NewNuclioZapTest("sec")
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
	opa := &secLocalOpa{allow: func(string, opaclient.Action) bool { return true }}
	abstractPlatform.OpaClient = opa

	writes := &secLocalWrites{}
	return &secLocalRig{
		platform: &Platform{Platform: abstractPlatform, projectsClient: writes},
		writes:   writes,
		opa:      opa,
	}
}

func secLocalPermissionOptions() opaclient.PermissionOptions {
	return opaclient.PermissionOptions{MemberIds: []string{"u-alice"}}
}

func secLocalRequireClientError(t *testing.T, err error) {
	t.Helper()
	if err == nil {
		t.Fatalf("operation was not refused")
	}
	if code := common.ResolveErrorStatusCodeOrDefault(err, http.StatusInternalServerError); code >= 500 {
		t.Fatalf("refusal is not a client error (status %d): %v", code, err)
	}
}

func TestSecLocalCreateWithoutPermission(t *testing.T) {
	rig := newSecLocalRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action) bool {
		return !(action == opaclient.ActionCreate && resource == "/projects/secret-project")
	}

	err := rig.platform.CreateProject(context.Background(), &platform.CreateProjectOptions{
		AuthSession:       &nop.Session{},
		ProjectConfig:     &platform.ProjectConfig{Meta: platform.ProjectMeta{Name: "secret-project", Namespace: secLocalNamespace}},
		PermissionOptions: secLocalPermissionOptions(),
	})
	secLocalRequireClientError(t, err)
	if rig.writes.creates != 0 {
		t.Fatalf("project was created despite the refusal")
	}
}

func TestSecLocalUpdateWithoutPermission(t *testing.T) {
	rig := newSecLocalRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action) bool {
		return !(action == opaclient.ActionUpdate && resource == "/projects/secret-project")
	}

	err := rig.platform.UpdateProject(context.Background(), &platform.UpdateProjectOptions{
		ProjectConfig: platform.ProjectConfig{
			Meta: platform.ProjectMeta{Name: "secret-project", Namespace: secLocalNamespace},
		},
		PermissionOptions: secLocalPermissionOptions(),
	})
	secLocalRequireClientError(t, err)
	if rig.writes.updates != 0 {
		t.Fatalf("project was updated despite the refusal")
	}
}

func TestSecLocalDeleteWithoutPermission(t *testing.T) {
	rig := newSecLocalRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action) bool {
		return !(action == opaclient.ActionDelete && resource == "/projects/secret-project")
	}

	err := rig.platform.DeleteProject(context.Background(), &platform.DeleteProjectOptions{
		AuthSession:       &nop.Session{},
		Meta:              platform.ProjectMeta{Name: "secret-project", Namespace: secLocalNamespace},
		PermissionOptions: secLocalPermissionOptions(),
	})
	secLocalRequireClientError(t, err)
	if rig.writes.deletes != 0 {
		t.Fatalf("project was deleted despite the refusal")
	}
}
