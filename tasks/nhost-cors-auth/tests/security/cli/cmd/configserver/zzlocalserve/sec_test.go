package zzlocalserve_test

// Security tests. A browser page may use the local configuration service only
// when the service grants the page's origin: the preflight before a JSON POST
// must not allow it and the response must not be readable by it. Independently
// of origins, no response may carry a secret value from the secrets file.

import (
	"strings"
	"testing"
)

// assertOriginRefused checks both halves of CORS for one foreign origin on one
// endpoint: the preflight (gates every JSON POST, so every change) and the
// readable response (gates every read).
func assertOriginRefused(t *testing.T, path, origin string) {
	t.Helper()

	p := newProject(t)
	s := startServer(t, p)

	pre := s.preflight(t, path, origin)
	if preflightAllows(pre, origin) {
		t.Errorf("preflight from %s to %s is allowed (status %d, Access-Control-Allow-Origin %q)",
			origin, path, pre.StatusCode, pre.Header.Values("Access-Control-Allow-Origin"))
	}

	query := `query { __typename }`
	var vars map[string]any
	if path == configPath {
		query = appSecretsQuery
		vars = map[string]any{"appID": s.appID(t)}
	}

	res := s.post(t, path, origin, query, vars)
	if grantsOrigin(res.resp, origin) {
		t.Errorf("response from %s is readable by %s (Access-Control-Allow-Origin %q)",
			path, origin, res.resp.Header.Values("Access-Control-Allow-Origin"))
	}

	// The project files are untouched.
	got := p.secretsOnDisk(t)
	for name, want := range p.values {
		if got[name] != want {
			t.Errorf("secret %s changed on disk", name)
		}
	}
}

func TestSecForeignWebsiteOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "https://evil.example")
}

func TestSecLookalikeHostEndingOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "https://local.dashboard.local.nhost.run.evil.example")
}

func TestSecOtherLocalServiceHostOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "https://attacker.local.nhost.run")
}

func TestSecNestedSubdomainOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "https://a.b.dashboard.local.nhost.run")
}

func TestSecLocalDevServerOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "http://localhost:3000")
}

func TestSecLogsAPIForeignWebsiteOrigin(t *testing.T) {
	assertOriginRefused(t, logsPath, "https://evil.example")
}

// containsAnySecret names the secrets whose real values appear in body.
func containsAnySecret(p *project, body []byte) []string {
	var found []string

	for name, v := range p.values {
		if strings.Contains(string(body), v) {
			found = append(found, name)
		}
	}

	return found
}

// Secret values listed by the service, asked by the dashboard itself.
func TestSecSecretListingHidesValues(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, appSecretsQuery, map[string]any{"appID": id})
	mustOK(t, res, "appSecrets")

	if found := containsAnySecret(p, res.body); len(found) > 0 {
		t.Errorf("appSecrets returns the values of %v", found)
	}

	res = s.post(t, configPath, dashboardLocal,
		`query { appsSecrets { appID secrets { name value } } }`, nil)
	mustOK(t, res, "appsSecrets")

	if found := containsAnySecret(p, res.body); len(found) > 0 {
		t.Errorf("appsSecrets returns the values of %v", found)
	}
}

// Configuration rendered with its secret references filled in.
func TestSecResolvedConfigHidesValues(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, `query ($appID: uuid!) {
	  config(appID: $appID, resolve: true) {
	    global { environment { name value } }
	    hasura { adminSecret webhookSecret jwtSecrets { type key } }
	    observability { grafana { adminPassword } }
	  }
	}`, map[string]any{"appID": id})
	if found := containsAnySecret(p, res.body); len(found) > 0 {
		t.Errorf("config(resolve: true) returns the values of %v", found)
	}

	res = s.post(t, configPath, dashboardLocal,
		`query ($appID: uuid!) { configRawJSON(appID: $appID, resolve: true) }`,
		map[string]any{"appID": id})
	if found := containsAnySecret(p, res.body); len(found) > 0 {
		t.Errorf("configRawJSON(resolve: true) returns the values of %v", found)
	}
}

// Pages in sandboxed frames and some redirects send the literal origin "null".
func TestSecNullOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "null")
}

// The dashboard domain itself, without a project subdomain label.
func TestSecBareDashboardDomainOrigin(t *testing.T) {
	assertOriginRefused(t, configPath, "https://dashboard.local.nhost.run")
}
