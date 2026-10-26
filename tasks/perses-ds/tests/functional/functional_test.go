package cwebenchtest

import (
	"strings"
	"testing"
)

// ---------------------------------------------------------------------------------------------
// A configuration that names no credential keeps saving and working for a caller who cannot read
// any secret.

func TestFunc_DatasourceWithoutSecretWorksForCallerWithoutSecretRead(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))
	code, body := e.request("POST", projectDatasourcesPath(), userEditor, projectDatasourceBody("plain", plugin))
	if !isSuccess(code) {
		t.Fatalf("a datasource naming no credential was refused: %d %s", code, body)
	}
	code, body = e.request("GET", savedProjectProxyPath("plain"), userEditor, "")
	if code != 200 {
		t.Fatalf("querying a datasource naming no credential failed: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 {
		t.Fatalf("expected exactly one request upstream, got %+v", calls)
	}
	if strings.HasPrefix(calls[0].Authorization, "Basic ") {
		t.Fatalf("a credential was attached where none was configured: %+v", calls[0])
	}
}

func TestFunc_UpdateWithoutSecretReferenceWorksForCallerWithoutSecretRead(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))
	e.mustOK("POST", projectDatasourcesPath(), userEditor, projectDatasourceBody("plain", plugin))
	updated := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, `"headers":{"X-Tenant":"shop"}`))
	code, body := e.request("PUT", projectDatasourcePath("plain"), userEditor, projectDatasourceBody("plain", updated))
	if !isSuccess(code) {
		t.Fatalf("updating a datasource that names no credential was refused: %d %s", code, body)
	}
}

// ---------------------------------------------------------------------------------------------
// A caller that may read a datasource but not the credential it names keeps querying it, because
// the reference was accepted from someone entitled to make it.

func TestFunc_ViewerQueriesSavedDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	e.mustOK("POST", projectDatasourcesPath(), userAuthor, projectDatasourceBody("shared", plugin))

	code, body := e.request("GET", savedProjectProxyPath("shared"), userViewer, "")
	if code != 200 {
		t.Fatalf("a reader of the datasource could not query it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 {
		t.Fatalf("expected exactly one request upstream, got %+v", calls)
	}
	if calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls[0])
	}
}

func TestFunc_ViewerQueriesSavedGlobalDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(globalSecret)))
	e.mustOK("POST", globalDatasourcesPath(), userGlobalAu, globalDatasourceBody("sharedglobal", plugin))

	code, body := e.request("GET", savedGlobalProxyPath("sharedglobal"), userGlobalView, "")
	if code != 200 {
		t.Fatalf("a reader of the global datasource could not query it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].Authorization != basic(globalBasicUser, globalBasicPass) {
		t.Fatalf("the stored global credential was not attached: %+v", calls)
	}
}

func TestFunc_ViewerQueriesSavedDashboardDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	e.mustOK("POST", dashboardsPath(), userAuthor, dashboardBody("sharedboard", "local", plugin))

	code, body := e.request("GET", savedDashboardProxyPath("sharedboard", "local"), userViewer, "")
	if code != 200 {
		t.Fatalf("a reader of the dashboard datasource could not query it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

func TestFunc_ViewerQueriesSavedEphemeralDashboardDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	e.mustOK("POST", ephemeralDashboardsPath(), userAuthor, ephemeralDashboardBody("sharedpreview", "local", plugin))

	code, body := e.request("GET", savedEphemeralProxyPath("sharedpreview", "local"), userViewer, "")
	if code != 200 {
		t.Fatalf("a reader of the ephemeral dashboard datasource could not query it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

// ---------------------------------------------------------------------------------------------
// A caller entitled to read the credential keeps referencing and using it.

func TestFunc_AuthorizedCallerSavesAndUsesDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", projectDatasourcesPath(), userAuthor, projectDatasourceBody("owned", plugin))
	if !isSuccess(code) {
		t.Fatalf("a caller entitled to the credential could not save it: %d %s", code, body)
	}
	code, body = e.request("GET", savedProjectProxyPath("owned"), userAuthor, "")
	if code != 200 {
		t.Fatalf("a caller entitled to the credential could not use it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

func TestFunc_AuthorizedCallerUsesUnsavedDatasourceReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", unsavedProjectProxyPath(), userAuthor, unsavedBody(plugin))
	if code != 200 {
		t.Fatalf("a caller entitled to the credential could not query with it: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

func TestFunc_HeaderSecretReferenceWorksForAuthorizedCaller(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, headerSecretReference("X-Api-Key", secretToken)))
	code, body := e.request("POST", projectDatasourcesPath(), userAuthor, projectDatasourceBody("headerowned", plugin))
	if !isSuccess(code) {
		t.Fatalf("a caller entitled to the credential could not save a reference in the connection settings: %d %s", code, body)
	}
	code, body = e.request("GET", savedProjectProxyPath("headerowned"), userAuthor, "")
	if code != 200 {
		t.Fatalf("the stored reference could not be used: %d %s", code, body)
	}
	calls := e.takeCalls()
	if len(calls) != 1 || calls[0].RemoteKey != projectToken {
		t.Fatalf("the stored credential did not reach the outbound request: %+v", calls)
	}
}

func TestFunc_AuthorizedCallerSavesDashboardReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", dashboardsPath(), userAuthor, dashboardBody("ownedboard", "local", plugin))
	if !isSuccess(code) {
		t.Fatalf("a caller entitled to the credential could not save a dashboard: %d %s", code, body)
	}
	code, body = e.request("GET", savedDashboardProxyPath("ownedboard", "local"), userAuthor, "")
	if code != 200 {
		t.Fatalf("the dashboard datasource could not be queried: %d %s", code, body)
	}
	if calls := e.takeCalls(); len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

func TestFunc_AuthorizedCallerSavesEphemeralDashboardReferencingSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", ephemeralDashboardsPath(), userAuthor, ephemeralDashboardBody("ownedpreview", "local", plugin))
	if !isSuccess(code) {
		t.Fatalf("a caller entitled to the credential could not save an ephemeral dashboard: %d %s", code, body)
	}
	code, body = e.request("GET", savedEphemeralProxyPath("ownedpreview", "local"), userAuthor, "")
	if code != 200 {
		t.Fatalf("the ephemeral dashboard datasource could not be queried: %d %s", code, body)
	}
	if calls := e.takeCalls(); len(calls) != 1 || calls[0].Authorization != basic(projectBasicUser, projectBasicPass) {
		t.Fatalf("the stored credential was not attached: %+v", calls)
	}
}

func TestFunc_UnauthenticatedCallerCannotUseDatasourceProxy(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))
	code, body := e.request("POST", unsavedProjectProxyPath(), "", unsavedBody(plugin))
	if !isClientError(code) {
		t.Fatalf("an unauthenticated request reached the proxy: %d %s", code, body)
	}
	e.requireNoUpstream()
}
