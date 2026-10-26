package cwebenchtest

import (
	"strings"
	"testing"
)

// ---------------------------------------------------------------------------------------------
// The report's trigger: a one-shot datasource description that names a credential the caller may
// not read. The server must not resolve it.

func TestSec_UnsavedProjectDatasourceUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", unsavedProjectProxyPath(), userEditor, unsavedBody(plugin))
	if !isClientError(code) {
		t.Fatalf("a request naming an unreadable credential was accepted: %d %s", code, body)
	}
	e.requireNoUpstream()
}

func TestSec_UnsavedGlobalDatasourceUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(globalSecret)))
	code, body := e.request("POST", unsavedGlobalProxyPath(), userGlobalEd, unsavedBody(plugin))
	if !isClientError(code) {
		t.Fatalf("a request naming an unreadable global credential was accepted: %d %s", code, body)
	}
	e.requireNoUpstream()
}

func TestSec_UnsavedDashboardDatasourceUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", unsavedDashboardProxyPath("dash"), userEditor, unsavedDashboardBody(plugin))
	if !isClientError(code) {
		t.Fatalf("a request naming an unreadable credential was accepted: %d %s", code, body)
	}
	e.requireNoUpstream()
}

// ---------------------------------------------------------------------------------------------
// Saving a configuration that names a credential the caller may not read, then using it.

func TestSec_SavedProjectDatasourceCreateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", projectDatasourcesPath(), userEditor, projectDatasourceBody("saved", plugin))
	if !isClientError(code) {
		t.Fatalf("a configuration naming an unreadable credential was saved: %d %s", code, body)
	}
	e.requireAbsent(projectDatasourcePath("saved"))
	e.requireNoUpstream()
}

func TestSec_SavedProjectDatasourceUpdateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	// An entitled author stores a datasource that names no credential.
	e.mustOK("POST", projectDatasourcesPath(), userAuthor, projectDatasourceBody("saved", pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))))
	e.takeCalls()

	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("PUT", projectDatasourcePath("saved"), userEditor, projectDatasourceBody("saved", plugin))
	if !isClientError(code) {
		t.Fatalf("an update naming an unreadable credential was accepted: %d %s", code, body)
	}
	// The refused update must not have changed the stored configuration.
	_, stored := e.request("GET", projectDatasourcePath("saved"), userOwner, "")
	if strings.Contains(stored, `"secret"`) {
		t.Fatalf("the refused update changed the stored configuration: %s", stored)
	}
	e.requireNoUpstream()
}

func TestSec_SavedGlobalDatasourceCreateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(globalSecret)))
	code, body := e.request("POST", globalDatasourcesPath(), userGlobalEd, globalDatasourceBody("savedglobal", plugin))
	if !isClientError(code) {
		t.Fatalf("a configuration naming an unreadable global credential was saved: %d %s", code, body)
	}
	e.requireAbsent(globalDatasourcePath("savedglobal"))
	e.requireNoUpstream()
}

func TestSec_SavedGlobalDatasourceUpdateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	e.mustOK("POST", globalDatasourcesPath(), userGlobalAu, globalDatasourceBody("savedglobal", pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))))
	e.takeCalls()

	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(globalSecret)))
	code, body := e.request("PUT", globalDatasourcePath("savedglobal"), userGlobalEd, globalDatasourceBody("savedglobal", plugin))
	if !isClientError(code) {
		t.Fatalf("an update naming an unreadable global credential was accepted: %d %s", code, body)
	}
	_, stored := e.request("GET", globalDatasourcePath("savedglobal"), userOwner, "")
	if strings.Contains(stored, `"secret"`) {
		t.Fatalf("the refused update changed the stored configuration: %s", stored)
	}
	e.requireNoUpstream()
}

// ---------------------------------------------------------------------------------------------
// The same protected outcome reached through a different kind of stored configuration.

func TestSec_DashboardCreateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", dashboardsPath(), userEditor, dashboardBody("board", "local", plugin))
	if !isClientError(code) {
		t.Fatalf("a dashboard naming an unreadable credential was saved: %d %s", code, body)
	}
	e.requireAbsent(dashboardPath("board"))
	e.requireNoUpstream()
}

func TestSec_DashboardUpdateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	e.mustOK("POST", dashboardsPath(), userAuthor, dashboardBody("board", "local", pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))))
	e.takeCalls()

	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("PUT", dashboardPath("board"), userEditor, dashboardBody("board", "local", plugin))
	if !isClientError(code) {
		t.Fatalf("a dashboard update naming an unreadable credential was accepted: %d %s", code, body)
	}
	_, stored := e.request("GET", dashboardPath("board"), userOwner, "")
	if strings.Contains(stored, `"secret"`) {
		t.Fatalf("the refused update changed the stored dashboard: %s", stored)
	}
	e.requireNoUpstream()
}

func TestSec_EphemeralDashboardCreateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("POST", ephemeralDashboardsPath(), userEditor, ephemeralDashboardBody("preview", "local", plugin))
	if !isClientError(code) {
		t.Fatalf("an ephemeral dashboard naming an unreadable credential was saved: %d %s", code, body)
	}
	e.requireAbsent(ephemeralDashboardPath("preview"))
	e.requireNoUpstream()
}

func TestSec_EphemeralDashboardUpdateUsesUnreadableSecret(t *testing.T) {
	e := newTestEnv(t)
	e.mustOK("POST", ephemeralDashboardsPath(), userAuthor, ephemeralDashboardBody("preview", "local", pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL))))
	e.takeCalls()

	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, secretReference(secretBasic)))
	code, body := e.request("PUT", ephemeralDashboardPath("preview"), userEditor, ephemeralDashboardBody("preview", "local", plugin))
	if !isClientError(code) {
		t.Fatalf("an ephemeral dashboard update naming an unreadable credential was accepted: %d %s", code, body)
	}
	_, stored := e.request("GET", ephemeralDashboardPath("preview"), userOwner, "")
	if strings.Contains(stored, `"secret"`) {
		t.Fatalf("the refused update changed the stored ephemeral dashboard: %s", stored)
	}
	e.requireNoUpstream()
}

// ---------------------------------------------------------------------------------------------
// A credential reference carried inside a value the proxy resolves, not in the field the report's
// example shows.

func TestSec_HeaderReferencedSecretOnUnsavedDatasource(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, headerSecretReference("X-Api-Key", secretToken)))
	code, body := e.request("POST", unsavedProjectProxyPath(), userEditor, unsavedBody(plugin))
	if !isClientError(code) {
		t.Fatalf("a request resolving an unreadable credential was accepted: %d %s", code, body)
	}
	e.requireNoUpstream()
}

func TestSec_HeaderReferencedSecretOnSavedDatasource(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, headerSecretReference("X-Api-Key", secretToken)))
	code, body := e.request("POST", projectDatasourcesPath(), userEditor, projectDatasourceBody("headerref", plugin))
	if !isClientError(code) {
		t.Fatalf("a configuration resolving an unreadable credential was saved: %d %s", code, body)
	}
	e.requireAbsent(projectDatasourcePath("headerref"))
	e.requireNoUpstream()
}

func TestSec_HeaderReferencedSecretOnDashboard(t *testing.T) {
	e := newTestEnv(t)
	plugin := pluginWithHTTPProxy(httpProxyConfig(e.upstream.URL, headerSecretReference("X-Api-Key", secretToken)))
	code, body := e.request("POST", dashboardsPath(), userEditor, dashboardBody("headerboard", "local", plugin))
	if !isClientError(code) {
		t.Fatalf("a dashboard resolving an unreadable credential was saved: %d %s", code, body)
	}
	e.requireAbsent(dashboardPath("headerboard"))
	e.requireNoUpstream()
}
