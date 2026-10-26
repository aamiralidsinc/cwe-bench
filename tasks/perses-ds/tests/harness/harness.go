// Shared harness for the hidden datasource-credential suites.
//
// Every test runs the product's real HTTP API: the same route registration, middleware, handlers,
// services and persistence that a deployed server uses. Only the permission authority is real too
// (native RBAC); the tests create users, roles and bindings and then speak HTTP with their tokens.
package cwebenchtest

import (
	"bytes"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"sync"
	"testing"

	"github.com/perses/perses/internal/api/core"
	"github.com/perses/perses/internal/api/dependency"
	apiConfig "github.com/perses/perses/pkg/model/api/config"
	v1 "github.com/perses/perses/pkg/model/api/v1"
	"github.com/perses/perses/pkg/model/api/v1/role"
	"github.com/perses/perses/pkg/model/api/v1/secret"
	commonSpec "github.com/perses/spec/go/common"
	"github.com/prometheus/client_golang/prometheus"
)

const (
	projectName = "shop"

	userOwner      = "owner"
	userEditor     = "editor"
	userAuthor     = "author"
	userViewer     = "viewer"
	userGlobalEd   = "globaleditor"
	userGlobalAu   = "globalauthor"
	userGlobalView = "globalviewer"

	// Credentials held by the stored secrets. They are the values an attacker must never be able
	// to make the server attach to an outbound request.
	projectBasicUser = "victim-user"
	projectBasicPass = "victim-password-1"
	projectToken     = "victim-token-4242"
	globalBasicUser  = "global-victim-user"
	globalBasicPass  = "global-victim-password-1"

	secretBasic  = "basic-credentials"
	secretToken  = "token-credentials"
	globalSecret = "global-credentials"
)

type upstreamCall struct {
	Method        string
	Path          string
	Authorization string
	RemoteKey     string
}

type testEnv struct {
	t        *testing.T
	server   *httptest.Server
	manager  dependency.Manager
	upstream *httptest.Server
	mu       sync.Mutex
	calls    []upstreamCall
	tokens   map[string]string
}

// workDir returns a directory for the server's own files. Trial and verifier containers can run with
// a tiny /tmp, so the caller may point PERSES_TEST_WORKDIR at a roomier filesystem.
func workDir(t *testing.T) string {
	t.Helper()
	base := os.Getenv("PERSES_TEST_WORKDIR")
	if base == "" {
		return t.TempDir()
	}
	if err := os.MkdirAll(base, 0o755); err != nil {
		t.Fatalf("cannot create the test work directory: %v", err)
	}
	dir, err := os.MkdirTemp(base, "perses-test-")
	if err != nil {
		t.Fatalf("cannot create the test work directory: %v", err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	return dir
}

func pluginArchives() string {
	if p := os.Getenv("PERSES_TEST_PLUGIN_ARCHIVES"); p != "" {
		return p
	}
	return "/opt/perses-plugins"
}

func newTestEnv(t *testing.T) *testEnv {
	t.Helper()
	conf := apiConfig.Config{
		Security: apiConfig.Security{
			Readonly:      false,
			EnableAuth:    true,
			EncryptionKey: secret.Hidden(hex.EncodeToString([]byte("=tW$56zytgB&3jN2E%7-+qrGZE?v6LCc"))),
			Authentication: apiConfig.AuthenticationConfig{
				AccessTokenTTL:  commonSpec.Duration(apiConfig.DefaultAccessTokenTTL),
				RefreshTokenTTL: commonSpec.Duration(apiConfig.DefaultRefreshTokenTTL),
				Providers:       apiConfig.AuthenticationProviders{EnableNative: true},
			},
			Authorization: apiConfig.AuthorizationConfig{
				Provider: apiConfig.AuthorizationProvider{
					Native: apiConfig.NativeAuthorizationProvider{Enable: true},
				},
			},
		},
		EphemeralDashboard: apiConfig.EphemeralDashboard{Enable: true},
		Plugin: apiConfig.Plugin{
			Path:         workDir(t),
			ArchivePaths: []string{pluginArchives()},
		},
		Database: apiConfig.Database{
			File: &apiConfig.File{Folder: workDir(t), Extension: apiConfig.JSONExtension, CaseSensitive: true},
		},
	}
	runner, manager, err := core.New(conf, false, prometheus.NewRegistry(), "")
	if err != nil {
		t.Fatalf("cannot start the product server: %v", err)
	}
	handler, err := runner.HTTPServerBuilder().BuildHandler()
	if err != nil {
		t.Fatalf("cannot build the product HTTP handler: %v", err)
	}
	server := httptest.NewServer(handler)
	t.Cleanup(func() {
		server.Close()
		_ = manager.Persistence().GetPersesDAO().Close()
	})

	e := &testEnv{t: t, server: server, manager: manager, tokens: map[string]string{}}
	e.upstream = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		e.mu.Lock()
		e.calls = append(e.calls, upstreamCall{
			Method:        r.Method,
			Path:          r.URL.Path,
			Authorization: r.Header.Get("Authorization"),
			RemoteKey:     r.Header.Get("X-Api-Key"),
		})
		e.mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	}))
	t.Cleanup(e.upstream.Close)

	for _, name := range []string{userOwner, userEditor, userAuthor, userViewer, userGlobalEd, userGlobalAu, userGlobalView} {
		e.tokens[name] = e.signUpAndLogin(name, "password-"+name)
	}
	e.installPermissions()
	e.mustOK("POST", "/api/v1/projects", userOwner, `{"kind":"Project","metadata":{"name":"`+projectName+`"},"spec":{}}`)
	e.mustOK("POST", "/api/v1/projects/"+projectName+"/secrets", userOwner,
		fmt.Sprintf(`{"kind":"Secret","metadata":{"name":%q,"project":%q},"spec":{"basicAuth":{"username":%q,"password":%q}}}`, secretBasic, projectName, projectBasicUser, projectBasicPass))
	e.mustOK("POST", "/api/v1/projects/"+projectName+"/secrets", userOwner,
		fmt.Sprintf(`{"kind":"Secret","metadata":{"name":%q,"project":%q},"spec":{"authorization":{"type":"Bearer","credentials":%q}}}`, secretToken, projectName, projectToken))
	e.mustOK("POST", "/api/v1/globalsecrets", userOwner,
		fmt.Sprintf(`{"kind":"GlobalSecret","metadata":{"name":%q},"spec":{"basicAuth":{"username":%q,"password":%q}}}`, globalSecret, globalBasicUser, globalBasicPass))
	return e
}

func (e *testEnv) signUpAndLogin(name, password string) string {
	e.t.Helper()
	code, body := e.request("POST", "/api/v1/users", "", fmt.Sprintf(`{"kind":"User","metadata":{"name":%q},"spec":{"nativeProvider":{"password":%q}}}`, name, password))
	if code != http.StatusOK {
		e.t.Fatalf("cannot create user %q: %d %s", name, code, body)
	}
	code, body = e.request("POST", "/api/auth/providers/native/login", "", fmt.Sprintf(`{"login":%q,"password":%q}`, name, password))
	if code != http.StatusOK {
		e.t.Fatalf("cannot log user %q in: %d %s", name, code, body)
	}
	var login struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.Unmarshal([]byte(body), &login); err != nil || login.AccessToken == "" {
		e.t.Fatalf("cannot read the access token of %q: %s", name, body)
	}
	return login.AccessToken
}

func permissions(actions []role.Action, scopes []role.Scope) v1.RoleSpec {
	return v1.RoleSpec{Permissions: []role.Permission{{Actions: actions, Scopes: scopes}}}
}

func (e *testEnv) put(entity any) {
	e.t.Helper()
	var err error
	switch obj := entity.(type) {
	case *v1.GlobalRole:
		err = e.manager.Persistence().GetGlobalRole().Update(obj)
	case *v1.GlobalRoleBinding:
		err = e.manager.Persistence().GetGlobalRoleBinding().Update(obj)
	case *v1.Role:
		err = e.manager.Persistence().GetRole().Update(obj)
	case *v1.RoleBinding:
		err = e.manager.Persistence().GetRoleBinding().Update(obj)
	default:
		e.t.Fatalf("unsupported setup entity %T", entity)
	}
	if err != nil {
		e.t.Fatalf("cannot store setup entity %T: %v", entity, err)
	}
}

func bindingSubjects(names ...string) []v1.Subject {
	subjects := make([]v1.Subject, 0, len(names))
	for _, name := range names {
		subjects = append(subjects, v1.Subject{Kind: v1.KindUser, Name: name})
	}
	return subjects
}

func (e *testEnv) installPermissions() {
	e.t.Helper()
	e.put(&v1.GlobalRole{Kind: v1.KindGlobalRole, Metadata: *v1.NewMetadata("super-admin"), Spec: permissions([]role.Action{role.WildcardAction}, []role.Scope{role.WildcardScope})})
	e.put(&v1.GlobalRoleBinding{Kind: v1.KindGlobalRoleBinding, Metadata: *v1.NewMetadata("super-admin"), Spec: v1.RoleBindingSpec{Role: "super-admin", Subjects: bindingSubjects(userOwner)}})

	e.put(&v1.Role{Kind: v1.KindRole, Metadata: *v1.NewProjectMetadata(projectName, "datasource-editor"), Spec: permissions(
		[]role.Action{role.CreateAction, role.ReadAction, role.UpdateAction},
		[]role.Scope{role.DatasourceScope, role.DashboardScope, role.EphemeralDashboardScope})})
	e.put(&v1.RoleBinding{Kind: v1.KindRoleBinding, Metadata: *v1.NewProjectMetadata(projectName, "datasource-editor"), Spec: v1.RoleBindingSpec{Role: "datasource-editor", Subjects: bindingSubjects(userEditor)}})

	e.put(&v1.Role{Kind: v1.KindRole, Metadata: *v1.NewProjectMetadata(projectName, "secret-author"), Spec: permissions(
		[]role.Action{role.ReadAction, role.CreateAction, role.UpdateAction},
		[]role.Scope{role.SecretScope, role.DatasourceScope, role.DashboardScope, role.EphemeralDashboardScope})})
	e.put(&v1.RoleBinding{Kind: v1.KindRoleBinding, Metadata: *v1.NewProjectMetadata(projectName, "secret-author"), Spec: v1.RoleBindingSpec{Role: "secret-author", Subjects: bindingSubjects(userAuthor)}})

	e.put(&v1.Role{Kind: v1.KindRole, Metadata: *v1.NewProjectMetadata(projectName, "datasource-viewer"), Spec: permissions(
		[]role.Action{role.ReadAction},
		[]role.Scope{role.DatasourceScope, role.DashboardScope, role.EphemeralDashboardScope})})
	e.put(&v1.RoleBinding{Kind: v1.KindRoleBinding, Metadata: *v1.NewProjectMetadata(projectName, "datasource-viewer"), Spec: v1.RoleBindingSpec{Role: "datasource-viewer", Subjects: bindingSubjects(userViewer)}})

	e.put(&v1.GlobalRole{Kind: v1.KindGlobalRole, Metadata: *v1.NewMetadata("global-editor"), Spec: permissions(
		[]role.Action{role.CreateAction, role.ReadAction, role.UpdateAction}, []role.Scope{role.GlobalDatasourceScope})})
	e.put(&v1.GlobalRoleBinding{Kind: v1.KindGlobalRoleBinding, Metadata: *v1.NewMetadata("global-editor"), Spec: v1.RoleBindingSpec{Role: "global-editor", Subjects: bindingSubjects(userGlobalEd)}})

	e.put(&v1.GlobalRole{Kind: v1.KindGlobalRole, Metadata: *v1.NewMetadata("global-author"), Spec: permissions(
		[]role.Action{role.CreateAction, role.ReadAction, role.UpdateAction}, []role.Scope{role.GlobalSecretScope, role.GlobalDatasourceScope})})
	e.put(&v1.GlobalRoleBinding{Kind: v1.KindGlobalRoleBinding, Metadata: *v1.NewMetadata("global-author"), Spec: v1.RoleBindingSpec{Role: "global-author", Subjects: bindingSubjects(userGlobalAu)}})

	e.put(&v1.GlobalRole{Kind: v1.KindGlobalRole, Metadata: *v1.NewMetadata("global-viewer"), Spec: permissions(
		[]role.Action{role.ReadAction}, []role.Scope{role.GlobalDatasourceScope})})
	e.put(&v1.GlobalRoleBinding{Kind: v1.KindGlobalRoleBinding, Metadata: *v1.NewMetadata("global-viewer"), Spec: v1.RoleBindingSpec{Role: "global-viewer", Subjects: bindingSubjects(userGlobalView)}})

	if err := e.manager.Service().GetAuthorization().RefreshPermissions(); err != nil {
		e.t.Fatalf("cannot refresh permissions: %v", err)
	}
}

func (e *testEnv) request(method, path, user, body string) (int, string) {
	e.t.Helper()
	var reader io.Reader
	if body != "" {
		reader = bytes.NewReader([]byte(body))
	}
	req, err := http.NewRequest(method, e.server.URL+path, reader)
	if err != nil {
		e.t.Fatalf("cannot build request %s %s: %v", method, path, err)
	}
	if body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	if token := e.tokens[user]; token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		e.t.Fatalf("%s %s: %v", method, path, err)
	}
	defer resp.Body.Close()
	payload, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(payload)
}

func (e *testEnv) mustOK(method, path, user, body string) string {
	e.t.Helper()
	code, payload := e.request(method, path, user, body)
	if code != http.StatusOK {
		e.t.Fatalf("setup %s %s failed: %d %s", method, path, code, payload)
	}
	return payload
}

func (e *testEnv) takeCalls() []upstreamCall {
	e.mu.Lock()
	defer e.mu.Unlock()
	calls := e.calls
	e.calls = nil
	return calls
}

// requireNoUpstream fails the test when the server sent anything to the upstream service, which is
// the direct evidence that the stored credential was put to use.
func (e *testEnv) requireNoUpstream() {
	e.t.Helper()
	if calls := e.takeCalls(); len(calls) != 0 {
		e.t.Fatalf("the server used the credential: the upstream service received %+v", calls)
	}
}

func isClientError(code int) bool { return code >= 400 && code < 500 }

// basic is the Authorization header the product sets for a basic-auth credential.
func basic(user, password string) string {
	return "Basic " + base64.StdEncoding.EncodeToString([]byte(user+":"+password))
}

func isSuccess(code int) bool { return code >= 200 && code < 300 }

// ---------------------------------------------------------------------------------------------
// Request bodies. They are the product's own user-facing API shapes.

func httpProxyConfig(url string, extra ...string) string {
	parts := []string{fmt.Sprintf(`"url":%q`, url)}
	parts = append(parts, extra...)
	return "{" + joinComma(parts) + "}"
}

func joinComma(parts []string) string {
	out := ""
	for i, part := range parts {
		if i > 0 {
			out += ","
		}
		out += part
	}
	return out
}

func secretReference(name string) string { return fmt.Sprintf(`"secret":%q`, name) }

func headerSecretReference(header, secretName string) string {
	return fmt.Sprintf(`"headers":{%q:"{{secret:%s}}"}}`, header, secretName)
}

func pluginWithHTTPProxy(proxyConfig string) string {
	return fmt.Sprintf(`{"kind":"PrometheusDatasource","spec":{"proxy":{"kind":"HTTPProxy","spec":%s}}}`, proxyConfig)
}

func projectDatasourceBody(name, plugin string) string {
	return fmt.Sprintf(`{"kind":"Datasource","metadata":{"name":%q,"project":%q},"spec":{"default":false,"plugin":%s}}`, name, projectName, plugin)
}

func globalDatasourceBody(name, plugin string) string {
	return fmt.Sprintf(`{"kind":"GlobalDatasource","metadata":{"name":%q},"spec":{"default":false,"plugin":%s}}`, name, plugin)
}

func localDatasource(name, plugin string) string {
	return fmt.Sprintf(`%q:{"default":false,"plugin":%s}`, name, plugin)
}

func dashboardBody(name, localName, plugin string) string {
	return fmt.Sprintf(`{"kind":"Dashboard","metadata":{"name":%q,"project":%q},"spec":{"datasources":{%s}}}`, name, projectName, localDatasource(localName, plugin))
}

func ephemeralDashboardBody(name, localName, plugin string) string {
	return fmt.Sprintf(`{"kind":"EphemeralDashboard","metadata":{"name":%q,"project":%q},"spec":{"ttl":"1h","duration":"5m","datasources":{%s}}}`, name, projectName, localDatasource(localName, plugin))
}

func unsavedBody(plugin string) string {
	return fmt.Sprintf(`{"method":"GET","spec":{"default":false,"plugin":%s}}`, plugin)
}

func unsavedDashboardBody(plugin string) string { return unsavedBody(plugin) }

// ---------------------------------------------------------------------------------------------
// Paths of the product's real HTTP endpoints.

func projectDatasourcesPath() string { return "/api/v1/projects/" + projectName + "/datasources" }
func projectDatasourcePath(name string) string {
	return "/api/v1/projects/" + projectName + "/datasources/" + name
}
func dashboardsPath() string { return "/api/v1/projects/" + projectName + "/dashboards" }
func dashboardPath(name string) string {
	return "/api/v1/projects/" + projectName + "/dashboards/" + name
}
func ephemeralDashboardsPath() string {
	return "/api/v1/projects/" + projectName + "/ephemeraldashboards"
}
func ephemeralDashboardPath(name string) string {
	return "/api/v1/projects/" + projectName + "/ephemeraldashboards/" + name
}
func globalDatasourcesPath() string           { return "/api/v1/globaldatasources" }
func globalDatasourcePath(name string) string { return "/api/v1/globaldatasources/" + name }

func savedProjectProxyPath(name string) string {
	return "/proxy/projects/" + projectName + "/datasources/" + name + "/api/v1/status/config"
}
func unsavedProjectProxyPath() string {
	return "/proxy/unsaved/projects/" + projectName + "/datasources/api/v1/status/config"
}
func savedDashboardProxyPath(dashboard, local string) string {
	return "/proxy/projects/" + projectName + "/dashboards/" + dashboard + "/datasources/" + local + "/api/v1/status/config"
}
func unsavedDashboardProxyPath(dashboard string) string {
	return "/proxy/unsaved/projects/" + projectName + "/dashboards/" + dashboard + "/datasources/api/v1/status/config"
}
func savedEphemeralProxyPath(dashboard, local string) string {
	return "/proxy/projects/" + projectName + "/ephemeraldashboards/" + dashboard + "/datasources/" + local + "/api/v1/status/config"
}
func savedGlobalProxyPath(name string) string {
	return "/proxy/globaldatasources/" + name + "/api/v1/status/config"
}
func unsavedGlobalProxyPath() string {
	return "/proxy/unsaved/globaldatasources/api/v1/status/config"
}

// requireAbsent fails when an entity was persisted despite the refusal.
func (e *testEnv) requireAbsent(path string) {
	e.t.Helper()
	code, body := e.request("GET", path, userOwner, "")
	if !isClientError(code) && code != http.StatusOK {
		e.t.Fatalf("GET %s returned %d %s", path, code, body)
	}
	if code == http.StatusOK {
		e.t.Fatalf("the request was refused but the configuration was persisted: GET %s returned %s", path, body)
	}
}
