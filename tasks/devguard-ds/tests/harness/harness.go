// Package hidden_harness builds the product's real router tree with stub
// dependencies so a request can be driven through the full middleware chain.
package hidden_harness

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/l3montree-dev/devguard/controllers"
	"github.com/l3montree-dev/devguard/controllers/dependencyfirewall"
	"github.com/l3montree-dev/devguard/database/models"
	"github.com/l3montree-dev/devguard/integrations/githubint"
	"github.com/l3montree-dev/devguard/integrations/gitlabint"
	"github.com/l3montree-dev/devguard/middlewares"
	"github.com/l3montree-dev/devguard/mocks"
	"github.com/l3montree-dev/devguard/router"
	"github.com/l3montree-dev/devguard/shared"
	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/mock"
)

const (
	OrgSlug     = "test-org"
	ProjectSlug = "test-project"
	AssetSlug   = "test-asset"
	VersionSlug = "test-ref"
	UserID      = "visitor-user"
)

// AC describes how the RBAC authority answers for the caller.
type AC struct {
	OrgMember  bool // HasAccess on the organization
	OrgRead    bool
	OrgWrite   bool
	ProjRead   bool
	ProjWrite  bool
	AssetRead  bool
	AssetWrite bool
}

// Options describe the scenario the router tree is built for.
type Options struct {
	AC            AC
	PublicOrg     bool
	PublicProject bool
	PublicAsset   bool
}

// Env is one built router tree.
type Env struct {
	E         *echo.Echo
	AC        *mocks.AccessControl
	Installs  *mocks.GithubAppInstallationRepository
	Aggregate *mocks.IntegrationAggregate
}

func newAC(cfg AC) *mocks.AccessControl {
	ac := &mocks.AccessControl{}
	ac.On("HasAccess", mock.Anything, mock.Anything).Return(cfg.OrgMember, nil)
	ac.On("GetAllMembersOfOrganization", mock.Anything).Return([]string{}, nil)
	ac.On("GetOwnerOfOrganization", mock.Anything).Return("", nil)
	ac.On("GetAllProjectsForUser", mock.Anything).Return([]string{}, nil)
	ac.On("GetAllAssetsForUser", mock.Anything).Return([]string{}, nil)

	ac.On("IsAllowed", mock.Anything, mock.Anything, mock.Anything, shared.ActionRead).Return(cfg.OrgRead, nil)
	ac.On("IsAllowed", mock.Anything, mock.Anything, mock.Anything, shared.ActionUpdate).Return(cfg.OrgWrite, nil)
	ac.On("IsAllowed", mock.Anything, mock.Anything, mock.Anything, shared.ActionCreate).Return(false, nil)
	ac.On("IsAllowed", mock.Anything, mock.Anything, mock.Anything, shared.ActionDelete).Return(false, nil)

	ac.On("IsAllowedInProject", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionRead).Return(cfg.ProjRead, nil)
	ac.On("IsAllowedInProject", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionUpdate).Return(cfg.ProjWrite, nil)
	ac.On("IsAllowedInProject", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionCreate).Return(cfg.ProjWrite, nil)
	ac.On("IsAllowedInProject", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionDelete).Return(cfg.ProjWrite, nil)

	ac.On("IsAllowedInAsset", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionRead).Return(cfg.AssetRead, nil)
	ac.On("IsAllowedInAsset", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionUpdate).Return(cfg.AssetWrite, nil)
	ac.On("IsAllowedInAsset", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionCreate).Return(cfg.AssetWrite, nil)
	ac.On("IsAllowedInAsset", mock.Anything, mock.Anything, mock.Anything, mock.Anything, shared.ActionDelete).Return(cfg.AssetWrite, nil)

	ac.On("IsAllowedInProject", mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	ac.On("IsAllowedInAsset", mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	ac.On("IsAllowed", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	return ac
}

type registry struct{ vals []reflect.Value }

func (r *registry) put(v any) { r.vals = append(r.vals, reflect.ValueOf(v)) }

// putAs registers v under the exact static type T (needed for interface args).
func putAs[T any](r *registry, v T) { r.vals = append(r.vals, reflect.ValueOf(&v).Elem()) }

func (r *registry) resolve(t reflect.Type) (reflect.Value, bool) {
	for _, v := range r.vals {
		if v.Type() == t {
			return v, true
		}
	}
	for _, v := range r.vals {
		if v.Type().AssignableTo(t) {
			return v, true
		}
	}
	return reflect.Value{}, false
}

func (r *registry) call(fn any) any {
	fv := reflect.ValueOf(fn)
	ft := fv.Type()
	in := make([]reflect.Value, ft.NumIn())
	for i := 0; i < ft.NumIn(); i++ {
		t := ft.In(i)
		v, ok := r.resolve(t)
		if !ok {
			panic(fmt.Sprintf("hidden_harness: no stub for parameter %d of %v (type %v)", i, ft, t))
		}
		in[i] = v
	}
	return fv.Call(in)[0].Interface()
}

// New builds the product's router tree for one scenario.
func New(t *testing.T, o Options) *Env {
	t.Helper()
	_ = os.Setenv("FRONTEND_URL", "http://localhost")
	_ = os.Setenv("GOTOOLCHAIN", "local")

	e := middlewares.Server()
	e.HTTPErrorHandler = func(err error, c echo.Context) {
		code := http.StatusInternalServerError
		if he, ok := err.(*echo.HTTPError); ok {
			code = he.Code
		}
		_ = c.NoContent(code)
	}

	orgID, projectID, assetID := uuid.New(), uuid.New(), uuid.New()
	ac := newAC(o.AC)

	pat := &mocks.PersonalAccessTokenService{}
	pat.On("VerifyRequestSignature", mock.Anything, mock.Anything).Return(UserID, "manage scan", nil)
	rbac := &mocks.RBACProvider{}
	rbac.On("GetDomainRBAC", mock.Anything).Return(ac)

	org := &models.Org{Model: models.Model{ID: orgID}, Slug: OrgSlug, IsPublic: o.PublicOrg}
	orgService := &mocks.OrgService{}
	orgService.On("ReadBySlug", mock.Anything, mock.Anything).Return(org, nil)

	project := models.Project{Model: models.Model{ID: projectID}, Slug: ProjectSlug, IsPublic: o.PublicProject}
	projectRepo := &mocks.ProjectRepository{}
	projectRepo.On("ReadBySlug", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(project, nil)

	asset := models.Asset{Model: models.Model{ID: assetID}, Slug: AssetSlug, IsPublic: o.PublicAsset}
	assetRepo := &mocks.AssetRepository{}
	assetRepo.On("ReadBySlug", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(asset, nil)

	version := models.AssetVersion{Name: VersionSlug, AssetID: assetID, LastAccessedAt: time.Now()}
	assetVersionRepo := &mocks.AssetVersionRepository{}
	assetVersionRepo.On("ReadBySlug", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(version, nil)

	vulnEventRepo := &mocks.VulnEventRepository{}
	vulnEventRepo.On("HasAccessToEvent", mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(true, nil)

	artifactRepo := &mocks.ArtifactRepository{}
	artifactRepo.On("ReadArtifact", mock.Anything, mock.Anything, mock.Anything, mock.Anything, mock.Anything).Return(models.Artifact{}, nil)

	extEntityService := &mocks.ExternalEntityProviderService{}
	extEntityService.On("SyncOrgs", mock.Anything).Return([]*models.Org{}, nil)
	extEntityService.On("TriggerOrgSync", mock.Anything).Return(nil)
	extEntityService.On("TriggerSync", mock.Anything).Return(nil)

	configService := &mocks.ConfigService{}
	configService.On("GetInstanceSettings", mock.Anything).Return(models.Config{}, os.ErrNotExist)

	publicClient := &mocks.PublicClient{}
	publicClient.On("GetIdentityFromCookie", mock.Anything, mock.Anything).Return(nil, os.ErrNotExist)

	installs := &mocks.GithubAppInstallationRepository{}
	installs.On("Read", mock.Anything, mock.Anything, mock.Anything).Return(models.GithubAppInstallation{}, nil)
	installs.On("Save", mock.Anything, mock.Anything, mock.Anything).Return(nil)
	github := githubint.NewGithubIntegration(installs, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil, nil)

	aggregate := &mocks.IntegrationAggregate{}
	aggregate.On("GetIntegration", shared.GitHubIntegrationID).Return(github)
	aggregate.On("GetIntegration", mock.Anything).Return(nil)
	aggregate.On("HandleEvent", mock.Anything, mock.Anything, mock.Anything).Return(nil)

	r := &registry{}
	apiV1 := router.APIV1Router{Group: e.Group("/api/v1")}
	apiV1.Group.Use(func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			shared.SetThirdPartyIntegration(c, aggregate)
			return next(c)
		}
	})
	r.put(apiV1)

	// controllers and repositories; putAs gives interface-typed values too.
	r.put(new(controllers.IntegrationController))
	r.put(new(controllers.OrgController))
	r.put(new(controllers.ScanController))
	r.put(new(controllers.AttestationController))
	r.put(new(controllers.PatController))
	r.put(new(controllers.ProjectController))
	r.put(new(controllers.PolicyController))
	r.put(new(controllers.WebhookController))
	r.put(new(controllers.StatisticsController))
	r.put(new(controllers.AssetController))
	r.put(new(controllers.DependencyVulnController))
	r.put(new(controllers.FirstPartyVulnController))
	r.put(new(controllers.ComplianceController))
	r.put(new(controllers.ComponentController))
	r.put(new(controllers.InToToController))
	r.put(new(controllers.VulnEventController))
	r.put(new(controllers.ArtifactController))
	r.put(new(controllers.ExternalReferenceController))
	r.put(new(controllers.AssetVersionController))
	r.put(new(controllers.LicenseRiskController))
	r.put(new(controllers.VEXRuleController))
	r.put(new(controllers.ReleaseController))
	r.put(new(controllers.CrowdsourcedVexingController))
	r.put(new(dependencyfirewall.DependencyProxyController))

	putAs[shared.PublicClient](r, publicClient)
	putAs[shared.PersonalAccessTokenService](r, pat)
	putAs[shared.ExternalEntityProviderService](r, extEntityService)
	putAs[shared.AssetRepository](r, assetRepo)
	putAs[shared.ProjectRepository](r, projectRepo)
	putAs[shared.AssetVersionRepository](r, assetVersionRepo)
	putAs[shared.ArtifactRepository](r, artifactRepo)
	putAs[shared.VulnEventRepository](r, vulnEventRepo)
	putAs[shared.RBACProvider](r, rbac)
	putAs[shared.OrgService](r, orgService)
	putAs[shared.ConfigService](r, configService)
	r.put(map[string]*gitlabint.GitlabOauth2Config{})

	session := r.call(router.NewSessionRouter)
	r.put(session)
	orgRouter := r.call(router.NewOrgRouter)
	r.put(orgRouter)
	projectRouter := r.call(router.NewProjectRouter)
	r.put(projectRouter)
	assetRouter := r.call(router.NewAssetRouter)
	r.put(assetRouter)
	assetVersionRouter := r.call(router.NewAssetVersionRouter)
	r.put(assetVersionRouter)
	r.call(router.NewDependencyVulnRouter)
	r.call(router.NewFirstPartyVulnRouter)
	r.call(router.NewLicenseRiskRouter)
	r.call(router.NewVEXRuleRouter)
	r.call(router.NewArtifactRouter)
	r.call(router.NewExternalReferenceRouter)
	r.call(router.NewCrowdsourcedVexingRouter)

	return &Env{E: e, AC: ac, Installs: installs, Aggregate: aggregate}
}

// Do drives one request through the real router tree and returns the recorder.
func (e *Env) Do(method, path, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	e.E.ServeHTTP(rec, req)
	return rec
}

// Status drives one request and returns its status code.
func (e *Env) Status(method, path, body string) int {
	return e.Do(method, path, body).Code
}

// Base is the asset-version path prefix.
func Base() string {
	return "/api/v1/organizations/" + OrgSlug + "/projects/" + ProjectSlug + "/assets/" + AssetSlug + "/refs/" + VersionSlug
}

// OrgBase is the organization path prefix.
func OrgBase() string { return "/api/v1/organizations/" + OrgSlug }

// ProjectBase is the project path prefix.
func ProjectBase() string { return OrgBase() + "/projects/" + ProjectSlug }

// UUID is a stable id used for path parameters that must parse.
const UUID = "11111111-1111-1111-1111-111111111111"
