//go:build test_unit

// Functional tests: legitimate project writes keep working after the authorization
// checks are added. They cover the coupled behaviours an over-broad fix would break:
// writes made with the deployment's configured trusted role, deployments running
// without an authorization service, and the ordinary allowed create / update / delete
// paths, including the extra project administration operations.

package kube

import (
	"context"
	"testing"
	"time"

	"github.com/nuclio/nuclio/pkg/auth/nop"
	"github.com/nuclio/nuclio/pkg/containerimagebuilderpusher"
	"github.com/nuclio/nuclio/pkg/platform"
	"github.com/nuclio/nuclio/pkg/platform/abstract"
	"github.com/nuclio/nuclio/pkg/platform/kube/apis/nuclio.io/v1beta1"
	"github.com/nuclio/nuclio/pkg/platform/kube/clients/kube"
	"github.com/nuclio/nuclio/pkg/platform/kube/clients/nuclio"
	mocks2 "github.com/nuclio/nuclio/pkg/platform/kube/clients/nuclio/clientset/mocks"
	mockplatform "github.com/nuclio/nuclio/pkg/platform/mock"
	"github.com/nuclio/nuclio/pkg/platformconfig"

	"github.com/nuclio/logger"
	"github.com/nuclio/opa-client"
	nucliozap "github.com/nuclio/zap"
	"github.com/stretchr/testify/mock"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/cache"
	"k8s.io/client-go/kubernetes/fake"
)

const funNamespace = "fun-namespace"

const funTrustedRole = "fun-trusted-role-value"

type funWrites struct {
	created []*v1beta1.NuclioProject
	updated []*v1beta1.NuclioProject
	deleted []string
}

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

type funRig struct {
	platform *Platform
	crd      *mocks2.NuclioProjectInterface
	writes   *funWrites
	logger   logger.Logger
}

func newFunRig(t *testing.T) *funRig {
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
	if abstractPlatform.ContainerBuilder, err = containerimagebuilderpusher.NewNop(logger, nil); err != nil {
		t.Fatalf("failed to create container builder: %v", err)
	}

	writes := &funWrites{}
	interfaceMock := &mocks2.Interface{}
	versionedMock := &mocks2.NuclioV1beta1Interface{}
	crd := &mocks2.NuclioProjectInterface{}
	interfaceMock.On("NuclioV1beta1").Return(versionedMock)
	versionedMock.On("NuclioProjects", funNamespace).Return(crd)

	crd.On("Get", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, name string, _ metav1.GetOptions) *v1beta1.NuclioProject {
			return &v1beta1.NuclioProject{
				ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: funNamespace},
			}
		}, nil).Maybe()
	crd.On("Create", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, project *v1beta1.NuclioProject, _ metav1.CreateOptions) *v1beta1.NuclioProject {
			writes.created = append(writes.created, project)
			return project
		}, nil).Maybe()
	crd.On("Update", mock.Anything, mock.Anything, mock.Anything).
		Return(func(_ context.Context, project *v1beta1.NuclioProject, _ metav1.UpdateOptions) *v1beta1.NuclioProject {
			writes.updated = append(writes.updated, project)
			return project
		}, nil).Maybe()
	crd.On("Delete", mock.Anything, mock.Anything, mock.Anything).
		Run(func(args mock.Arguments) {
			writes.deleted = append(writes.deleted, args.String(1))
		}).Return(nil).Maybe()
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

	return &funRig{platform: kubePlatform, crd: crd, writes: writes, logger: logger}
}

func funProjectConfig(name string) *platform.ProjectConfig {
	return &platform.ProjectConfig{
		Meta: platform.ProjectMeta{Name: name, Namespace: funNamespace},
		Spec: platform.ProjectSpec{Description: "some description"},
	}
}

func TestFuncKubeAllowedCreateUpdateDelete(t *testing.T) {
	rig := newFunRig(t)
	ctx := context.Background()

	if err := rig.platform.CreateProject(ctx, &platform.CreateProjectOptions{
		AuthSession:       &nop.Session{},
		ProjectConfig:     funProjectConfig("my-project"),
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed create failed: %v", err)
	}
	if len(rig.writes.created) != 1 || rig.writes.created[0].Name != "my-project" {
		t.Fatalf("create did not reach the project storage: %+v", rig.writes.created)
	}

	if err := rig.platform.UpdateProject(ctx, &platform.UpdateProjectOptions{
		ProjectConfig:     *funProjectConfig("my-project"),
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed update failed: %v", err)
	}
	if len(rig.writes.updated) != 1 || rig.writes.updated[0].Name != "my-project" {
		t.Fatalf("update did not reach the project storage: %+v", rig.writes.updated)
	}

	if err := rig.platform.DeleteProject(ctx, &platform.DeleteProjectOptions{
		AuthSession:       &nop.Session{},
		Meta:              platform.ProjectMeta{Name: "my-project", Namespace: funNamespace},
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed delete failed: %v", err)
	}
	if len(rig.writes.deleted) != 1 || rig.writes.deleted[0] != "my-project" {
		t.Fatalf("delete did not reach the project storage: %+v", rig.writes.deleted)
	}
}

func TestFuncKubeTrustedRoleCreate(t *testing.T) {
	rig := newFunRig(t)
	rig.platform.OpaClient = opaclient.NewHTTPClient(rig.logger,
		"http://127.0.0.1:1",
		"/v1/data/authz/allow",
		"/v1/data/authz/filter_allowed",
		time.Second,
		false,
		funTrustedRole,
		false)

	if err := rig.platform.CreateProject(context.Background(), &platform.CreateProjectOptions{
		AuthSession:   &nop.Session{},
		ProjectConfig: funProjectConfig("leader-project"),
		PermissionOptions: opaclient.PermissionOptions{
			OverrideHeaderValue: funTrustedRole,
		},
	}); err != nil {
		t.Fatalf("create with the trusted role failed: %v", err)
	}
	if len(rig.writes.created) != 1 {
		t.Fatalf("create with the trusted role did not reach the project storage")
	}
}

func TestFuncKubeNoPolicyService(t *testing.T) {
	rig := newFunRig(t)
	rig.platform.OpaClient = opaclient.NewNopClient(rig.logger, false)

	if err := rig.platform.UpdateProject(context.Background(), &platform.UpdateProjectOptions{
		ProjectConfig: *funProjectConfig("my-project"),
	}); err != nil {
		t.Fatalf("update without an authorization service failed: %v", err)
	}
	if len(rig.writes.updated) != 1 {
		t.Fatalf("update without an authorization service did not reach the project storage")
	}
}

func TestFuncKubeRename(t *testing.T) {
	rig := newFunRig(t)

	if err := rig.platform.RenameProject(context.Background(), &platform.RenameProjectOptions{
		Meta:              platform.ProjectMeta{Name: "old-name", Namespace: funNamespace},
		NewName:           "new-name",
		AuthSession:       &nop.Session{},
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed rename failed: %v", err)
	}
	if len(rig.writes.created) != 1 || rig.writes.created[0].Name != "new-name" {
		t.Fatalf("renamed project was not created under the new name: %+v", rig.writes.created)
	}
	if len(rig.writes.deleted) != 1 || rig.writes.deleted[0] != "old-name" {
		t.Fatalf("project was not removed under the old name: %+v", rig.writes.deleted)
	}
}

func TestFuncKubeUpdateStatus(t *testing.T) {
	rig := newFunRig(t)

	if err := rig.platform.UpdateProjectStatus(context.Background(), &platform.UpdateProjectStatusOptions{
		Meta:              platform.ProjectMeta{Name: "my-project", Namespace: funNamespace},
		AdminStatus:       "offline",
		AuthSession:       &nop.Session{},
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed status update failed: %v", err)
	}
	if len(rig.writes.updated) != 1 {
		t.Fatalf("status update did not reach the project storage")
	}
	if rig.writes.updated[0].Status.AdminStatus != "offline" {
		t.Fatalf("project status was not stored: %+v", rig.writes.updated[0].Status)
	}
}

func TestFuncKubeCreateAndWait(t *testing.T) {
	rig := newFunRig(t)

	project, err := platform.NewAbstractProject(rig.logger, rig.platform, *funProjectConfig("imported-project"))
	if err != nil {
		t.Fatalf("failed to create project instance: %v", err)
	}
	if err := project.CreateAndWait(context.Background(), &platform.CreateProjectOptions{
		ProjectConfig:     project.GetConfig(),
		AuthSession:       &nop.Session{},
		PermissionOptions: opaclient.PermissionOptions{MemberIds: []string{"u-alice"}},
	}); err != nil {
		t.Fatalf("allowed create-and-wait failed: %v", err)
	}
	if len(rig.writes.created) != 1 || rig.writes.created[0].Name != "imported-project" {
		t.Fatalf("create-and-wait did not reach the project storage: %+v", rig.writes.created)
	}
}
