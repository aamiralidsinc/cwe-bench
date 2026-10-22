package zzlocalserve_test

// Functional tests: the local dashboard keeps working against the service.

import (
	"net/http"
	"os"
	"sort"
	"strings"
	"testing"
)

// The dashboard's own origins: both host forms, http or https, any port.
func TestFuncDashboardOriginsAllowed(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	origins := []string{
		"https://local.dashboard.local.nhost.run",
		"http://local.dashboard.local.nhost.run",
		"https://local.dashboard.local.nhost.run:1337",
		"https://myproject.dashboard.local.nhost.run:8443",
		"https://local.dashboard.nhost.run",
		"http://local.dashboard.nhost.run:443",
	}

	for _, origin := range origins {
		t.Run(strings.NewReplacer("://", "_", ":", "_", ".", "_").Replace(origin), func(t *testing.T) {
			pre := s.preflight(t, configPath, origin)
			if !preflightAllows(pre, origin) {
				t.Errorf("preflight from dashboard origin %s refused: status %d headers %v",
					origin, pre.StatusCode, pre.Header)
			}

			res := s.post(t, configPath, origin, appSecretsQuery, map[string]any{"appID": id})
			mustOK(t, res, "appSecrets from "+origin)

			if !grantsOrigin(res.resp, origin) {
				t.Errorf("response not readable by dashboard origin %s: %v", origin, res.resp.Header)
			}

			logsPre := s.preflight(t, logsPath, origin)
			if !preflightAllows(logsPre, origin) {
				t.Errorf("logs preflight from dashboard origin %s refused: status %d", origin, logsPre.StatusCode)
			}

			logs := s.post(t, logsPath, origin, `query { __typename }`, nil)
			if logs.resp.StatusCode != http.StatusOK || !grantsOrigin(logs.resp, origin) {
				t.Errorf("logs API not usable from %s: status %d headers %v", origin, logs.resp.StatusCode, logs.resp.Header)
			}
		})
	}
}

// Tools that send no Origin header (curl, scripts) still work.
func TestFuncRequestWithoutOrigin(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, "", appSecretsQuery, map[string]any{"appID": id})
	mustOK(t, res, "appSecrets without Origin")
}

func TestFuncSecretNamesListed(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, appSecretsQuery, map[string]any{"appID": id})
	mustOK(t, res, "appSecrets")

	got := secretList(t, res.data["appSecrets"])
	names := make([]string, 0, len(got))
	for n := range got {
		names = append(names, n)
	}
	sort.Strings(names)

	want := append([]string(nil), secretNames...)
	sort.Strings(want)

	if strings.Join(names, ",") != strings.Join(want, ",") {
		t.Errorf("secret names = %v, want %v", names, want)
	}
}

// assertOthersKept checks every secret except skip keeps its original value.
func assertOthersKept(t *testing.T, p *project, got map[string]string, skip ...string) {
	t.Helper()

	for name, want := range p.values {
		skipped := false
		for _, s := range skip {
			if s == name {
				skipped = true
			}
		}

		if skipped {
			continue
		}

		if got[name] != want {
			t.Errorf("secret %s on disk = %q, want its original value %q", name, got[name], want)
		}
	}
}

const updateSecretMutation = `mutation ($appID: uuid!, $s: ConfigEnvironmentVariableInsertInput!) {
  updateSecret(appID: $appID, secret: $s) { name }
}`

func TestFuncUpdateSecretKeepsOthers(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	newValue := randomValue(t, "newv")
	res := s.post(t, configPath, dashboardLocal, updateSecretMutation, map[string]any{
		"appID": id,
		"s":     map[string]any{"name": "NHOST_WEBHOOK_SECRET", "value": newValue},
	})
	mustOK(t, res, "updateSecret")

	got := p.secretsOnDisk(t)
	if got["NHOST_WEBHOOK_SECRET"] != newValue {
		t.Errorf("updated secret on disk = %q, want %q", got["NHOST_WEBHOOK_SECRET"], newValue)
	}

	if len(got) != len(p.values) {
		t.Errorf("secrets file has %d entries, want %d: %v", len(got), len(p.values), got)
	}

	assertOthersKept(t, p, got, "NHOST_WEBHOOK_SECRET")
}

// Two edits in a row from the dashboard: both land, nothing else changes.
func TestFuncSuccessiveSecretEdits(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	first := randomValue(t, "first")
	second := randomValue(t, "second")

	mustOK(t, s.post(t, configPath, dashboardLocal, updateSecretMutation, map[string]any{
		"appID": id,
		"s":     map[string]any{"name": "STRIPE_SECRET_KEY", "value": first},
	}), "first updateSecret")

	mustOK(t, s.post(t, configPath, dashboardLocal, updateSecretMutation, map[string]any{
		"appID": id,
		"s":     map[string]any{"name": "GRAFANA_ADMIN_PASSWORD", "value": second},
	}), "second updateSecret")

	got := p.secretsOnDisk(t)
	if got["STRIPE_SECRET_KEY"] != first {
		t.Errorf("first edit lost: %q, want %q", got["STRIPE_SECRET_KEY"], first)
	}

	if got["GRAFANA_ADMIN_PASSWORD"] != second {
		t.Errorf("second edit lost: %q, want %q", got["GRAFANA_ADMIN_PASSWORD"], second)
	}

	assertOthersKept(t, p, got, "STRIPE_SECRET_KEY", "GRAFANA_ADMIN_PASSWORD")
}

func TestFuncInsertSecretKeepsOthers(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	value := randomValue(t, "ins")
	res := s.post(t, configPath, dashboardLocal, `mutation ($appID: uuid!, $s: ConfigEnvironmentVariableInsertInput!) {
	  insertSecret(appID: $appID, secret: $s) { name }
	}`, map[string]any{
		"appID": id,
		"s":     map[string]any{"name": "NEW_SERVICE_TOKEN", "value": value},
	})
	mustOK(t, res, "insertSecret")

	got := p.secretsOnDisk(t)
	if got["NEW_SERVICE_TOKEN"] != value {
		t.Errorf("inserted secret on disk = %q, want %q", got["NEW_SERVICE_TOKEN"], value)
	}

	assertOthersKept(t, p, got)
}

func TestFuncDeleteSecretKeepsOthers(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, `mutation ($appID: uuid!, $k: String!) {
	  deleteSecret(appID: $appID, key: $k) { name }
	}`, map[string]any{"appID": id, "k": "UNUSED_API_TOKEN"})
	mustOK(t, res, "deleteSecret")

	got := p.secretsOnDisk(t)
	if _, ok := got["UNUSED_API_TOKEN"]; ok {
		t.Errorf("deleted secret still on disk")
	}

	assertOthersKept(t, p, got, "UNUSED_API_TOKEN")
}

// The dashboard reads service versions and settings from the resolved
// configuration.
func TestFuncResolvedConfigSettings(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, `query ($appID: uuid!) {
	  config(appID: $appID, resolve: true) {
	    hasura { version }
	    auth { version redirections { clientUrl } }
	    postgres { version }
	    storage { version }
	  }
	}`, map[string]any{"appID": id})
	mustOK(t, res, "config(resolve: true)")

	for _, want := range []string{"v2.46.0-ce", "0.44.2", "http://localhost:3000", "14.20-20251217-1", "0.9.1"} {
		if !strings.Contains(string(res.body), want) {
			t.Errorf("resolved config lacks %q: %s", want, res.body)
		}
	}
}

// The unresolved configuration shows the secret references as written.
func TestFuncUnresolvedConfigShowsReferences(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, `query ($appID: uuid!) {
	  config(appID: $appID, resolve: false) { hasura { adminSecret webhookSecret } }
	}`, map[string]any{"appID": id})
	mustOK(t, res, "config(resolve: false)")

	for _, want := range []string{
		"{{ secrets.HASURA_GRAPHQL_ADMIN_SECRET }}",
		"{{ secrets.NHOST_WEBHOOK_SECRET }}",
	} {
		if !strings.Contains(string(res.body), want) {
			t.Errorf("unresolved config lacks %q: %s", want, res.body)
		}
	}
}

// Editing configuration from the dashboard persists it, keeps the secret
// references, and leaves the secrets file alone.
func TestFuncUpdateConfigKeepsReferences(t *testing.T) {
	p := newProject(t)
	s := startServer(t, p)
	id := s.appID(t)

	res := s.post(t, configPath, dashboardLocal, `mutation ($appID: uuid!, $c: ConfigConfigUpdateInput!) {
	  updateConfig(appID: $appID, config: $c) { auth { redirections { clientUrl } } }
	}`, map[string]any{
		"appID": id,
		"c": map[string]any{
			"auth": map[string]any{"redirections": map[string]any{"clientUrl": "http://localhost:4000"}},
		},
	})
	mustOK(t, res, "updateConfig")

	b, err := os.ReadFile(p.configFile)
	if err != nil {
		t.Fatalf("read config: %v", err)
	}

	cfg := string(b)
	if !strings.Contains(cfg, "http://localhost:4000") {
		t.Errorf("config change not persisted:\n%s", cfg)
	}

	if !strings.Contains(cfg, "{{ secrets.HASURA_GRAPHQL_ADMIN_SECRET }}") {
		t.Errorf("secret reference lost from config file:\n%s", cfg)
	}

	assertOthersKept(t, p, p.secretsOnDisk(t))
}
