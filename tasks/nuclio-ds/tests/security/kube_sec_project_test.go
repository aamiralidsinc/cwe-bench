//go:build test_unit

// Security tests: every operation the product offers for writing a project must ask the
// deployment's authorization service about the project it is about to write and must
// refuse, with no side effect, when the caller is not allowed. The tests drive the real
// platform API that the dashboard and the CLI use. They never assert a particular
// refusal status: any client error plus the absence of the write is enough.

package kube

import (
	"context"
	"net/http"
	"testing"

	"github.com/nuclio/nuclio/pkg/auth/nop"
	"github.com/nuclio/nuclio/pkg/common"
	"github.com/nuclio/nuclio/pkg/containerimagebuilderpusher"
	"github.com/nuclio/nuclio/pkg/platform"
	"github.com/nuclio/nuclio/pkg/platform/abstract"
	"github.com/nuclio/nuclio/pkg/platform/kube/apis/nuclio.io/v1beta1"
	"github.com/nuclio/nuclio/pkg/platform/kube/clients/kube"
	"github.com/nuclio/nuclio/pkg/platform/kube/clients/nuclio"
	mocks2 "github.com/nuclio/nuclio/pkg/platform/kube/clients/nuclio/clientset/mocks"
	mockplatform "github.com/nuclio/nuclio/pkg/platform/mock"
	"github.com/nuclio/nuclio/pkg/platformconfig"

	"github.com/nuclio/opa-client"
	nucliozap "github.com/nuclio/zap"
	"github.com/stretchr/testify/mock"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/cache"
	"k8s.io/client-go/kubernetes/fake"
)

const secNamespace = "sec-namespace"

type secOpa struct {
	allow func(resource string, action opaclient.Action, ids []string) bool
}

func (s *secOpa) QueryPermissions(_ context.Context,
	resource string,
	action opaclient.Action,
	options *opaclient.PermissionOptions) (bool, error) {
	return s.allow(resource, action, options.MemberIds), nil
}

func (s *secOpa) QueryPermissionsMultiResources(_ context.Context,
	resources []string,
	action opaclient.Action,
	options *opaclient.PermissionOptions) ([]bool, error) {
	allowed := make([]bool, len(resources))
	for i, resource := range resources {
		allowed[i] = s.allow(resource, action, options.MemberIds)
	}
	return allowed, nil
}

type secRig struct {
	platform *Platform
	crd      *mocks2.NuclioProjectInterface
	opa      *secOpa
}

func newSecRig(t *testing.T) *secRig {
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
		Return([]platform.Project{}, nil).Maybe()
	mockedPlatform.On("GetFunctions", mock.Anything, mock.Anything).
		Return([]platform.Function{}, nil).Maybe()
	mockedPlatform.On("GetAPIGateways", mock.Anything, mock.Anything).
		Return([]platform.APIGateway{}, nil).Maybe()

	abstractPlatform, err := abstract.NewPlatform(logger, mockedPlatform, config, "")
	if err != nil {
		t.Fatalf("failed to create abstract platform: %v", err)
	}
	opa := &secOpa{allow: func(string, opaclient.Action, []string) bool { return true }}
	abstractPlatform.OpaClient = opa
	if abstractPlatform.ContainerBuilder, err = containerimagebuilderpusher.NewNop(logger, nil); err != nil {
		t.Fatalf("failed to create container builder: %v", err)
	}

	interfaceMock := &mocks2.Interface{}
	versionedMock := &mocks2.NuclioV1beta1Interface{}
	crd := &mocks2.NuclioProjectInterface{}
	interfaceMock.On("NuclioV1beta1").Return(versionedMock)
	versionedMock.On("NuclioProjects", secNamespace).Return(crd)

	crd.On("Get", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, name string, _ metav1.GetOptions) *v1beta1.NuclioProject {
			return &v1beta1.NuclioProject{
				ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: secNamespace},
			}
		}, nil).Maybe()
	crd.On("Create", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, project *v1beta1.NuclioProject, _ metav1.CreateOptions) *v1beta1.NuclioProject {
			return project
		}, nil).Maybe()
	crd.On("Update", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, project *v1beta1.NuclioProject, _ metav1.UpdateOptions) *v1beta1.NuclioProject {
			return project
		}, nil).Maybe()
	crd.On("Delete", mock.Anything, mock.Anything, mock.Anything).Return(nil).Maybe()
	crd.On("List", mock.Anything, mock.Anything).Return(&v1beta1.NuclioProjectList{}, nil).Maybe()

	kubePlatform := &Platform{
		Platform: abstractPlatform,
		consumer: &nuclio.Consumer{
			NuclioClientSet: nuclio.NewClientWithRetryFromClient(interfaceMock),
			KubeClientSet:   kube.NewClientWithRetryFromClient(fake.NewSimpleClientset()),
		},
		projectsCache: cache.NewExpiring(),
	}
	kubePlatform.projectsClient, err = NewProjectsClient(kubePlatform, config)
	if err != nil {
		t.Fatalf("failed to create projects client: %v", err)
	}

	return &secRig{platform: kubePlatform, crd: crd, opa: opa}
}

func secPermissionOptions() opaclient.PermissionOptions {
	return opaclient.PermissionOptions{MemberIds: []string{"u-alice"}}
}

func secRequireClientError(t *testing.T, err error) {
	t.Helper()
	if err == nil {
		t.Fatalf("operation was not refused")
	}
	if code := common.ResolveErrorStatusCodeOrDefault(err, http.StatusInternalServerError); code >= 500 {
		t.Fatalf("refusal is not a client error (status %d): %v", code, err)
	}
}

func TestSecKubeCreateWithoutPermission(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		return !(action == opaclient.ActionCreate && resource == "/projects/secret-project")
	}

	err := rig.platform.CreateProject(context.Background(), &platform.CreateProjectOptions{
		AuthSession:   &nop.Session{},
		ProjectConfig: &platform.ProjectConfig{Meta: platform.ProjectMeta{Name: "secret-project", Namespace: secNamespace}},
		PermissionOptions: secPermissionOptions(),
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Create", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeUpdateWithoutPermission(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		return !(action == opaclient.ActionUpdate && resource == "/projects/secret-project")
	}

	err := rig.platform.UpdateProject(context.Background(), &platform.UpdateProjectOptions{
		ProjectConfig: platform.ProjectConfig{
			Meta: platform.ProjectMeta{Name: "secret-project", Namespace: secNamespace},
		},
		PermissionOptions: secPermissionOptions(),
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Get", mock.Anything, mock.Anything, mock.Anything)
	rig.crd.AssertNotCalled(t, "Update", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeDeleteWithoutPermission(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		return !(action == opaclient.ActionDelete && resource == "/projects/secret-project")
	}

	err := rig.platform.DeleteProject(context.Background(), &platform.DeleteProjectOptions{
		AuthSession: &nop.Session{},
		Meta:        platform.ProjectMeta{Name: "secret-project", Namespace: secNamespace},
		PermissionOptions: secPermissionOptions(),
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Delete", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeImportCreateWithoutPermission(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		return !(action == opaclient.ActionCreate && resource == "/projects/imported-project")
	}

	project, err := platform.NewAbstractProject(rig.platform.Logger, rig.platform, platform.ProjectConfig{
		Meta: platform.ProjectMeta{Name: "imported-project", Namespace: secNamespace},
	})
	if err != nil {
		t.Fatalf("failed to create project instance: %v", err)
	}
	err = project.CreateAndWait(context.Background(), &platform.CreateProjectOptions{
		ProjectConfig:     project.GetConfig(),
		AuthSession:       &nop.Session{},
		PermissionOptions: opaclient.PermissionOptions{},
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Create", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeRenameWithoutPermissionOnNewName(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		return !(action == opaclient.ActionCreate && resource == "/projects/someone-elses-project")
	}

	err := rig.platform.RenameProject(context.Background(), &platform.RenameProjectOptions{
		Meta:              platform.ProjectMeta{Name: "editable-project", Namespace: secNamespace},
		NewName:           "someone-elses-project",
		AuthSession:       &nop.Session{},
		PermissionOptions: secPermissionOptions(),
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Create", mock.Anything, mock.Anything, mock.Anything)
	rig.crd.AssertNotCalled(t, "Delete", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeStatusWithoutPermission(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, _ []string) bool {
		isSecret := resource == "/projects/secret-project"
		return !(isSecret && (action == opaclient.ActionUpdate || action == opaclient.ActionDelete))
	}

	err := rig.platform.UpdateProjectStatus(context.Background(), &platform.UpdateProjectStatusOptions{
		Meta:              platform.ProjectMeta{Name: "secret-project", Namespace: secNamespace},
		AdminStatus:       "offline",
		AuthSession:       &nop.Session{},
		PermissionOptions: secPermissionOptions(),
	})
	secRequireClientError(t, err)
	rig.crd.AssertNotCalled(t, "Update", mock.Anything, mock.Anything, mock.Anything)
}

func TestSecKubeCallerIdentityIsUsed(t *testing.T) {
	rig := newSecRig(t)
	rig.opa.allow = func(resource string, action opaclient.Action, ids []string) bool {
		if resource != "/projects/shared-project" || action != opaclient.ActionUpdate {
			return true
		}
		for _, id := range ids {
			if id == "u-alice" {
				return true
			}
		}
		return false
	}

	updateOptions := func(memberID string) *platform.UpdateProjectOptions {
		return &platform.UpdateProjectOptions{
			ProjectConfig: platform.ProjectConfig{
				Meta: platform.ProjectMeta{Name: "shared-project", Namespace: secNamespace},
			},
			PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{memberID}},
		}
	}

	// the caller the policy allows still writes
	if err := rig.platform.UpdateProject(context.Background(), updateOptions("u-alice")); err != nil {
		t.Fatalf("allowed caller was refused: %v", err)
	}
	rig.crd.AssertNumberOfCalls(t, "Update", 1)

	// a different caller, whose identity the policy denies, must not write
	err := rig.platform.UpdateProject(context.Background(), updateOptions("u-bob"))
	secRequireClientError(t, err)
	rig.crd.AssertNumberOfCalls(t, "Update", 1)
}
