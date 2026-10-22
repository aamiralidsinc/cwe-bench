package zzlocalserve_test

// Shared helpers for the hidden tests. They start the real `configserver`
// command (the one `nhost dev up` runs for the local dashboard) on a loopback
// port with a throw-away project, and talk to it over HTTP like a browser.
// Expected values and file checks are computed here, never with product code.

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/nhost/nhost/cli/cmd/configserver"
	"github.com/pelletier/go-toml/v2"
)

const (
	configPath     = "/v1/configserver/graphql"
	logsPath       = "/v1/logs/graphql"
	dashboardLocal = "https://local.dashboard.local.nhost.run"
)

// projectConfig is a regular project configuration whose sensitive settings
// point at entries of the secrets file.
const projectConfig = `[global]
[[global.environment]]
name = 'STRIPE_SECRET_KEY'
value = '{{ secrets.STRIPE_SECRET_KEY }}'

[hasura]
version = 'v2.46.0-ce'
adminSecret = '{{ secrets.HASURA_GRAPHQL_ADMIN_SECRET }}'
webhookSecret = '{{ secrets.NHOST_WEBHOOK_SECRET }}'

[[hasura.jwtSecrets]]
type = 'HS256'
key = '{{ secrets.HASURA_GRAPHQL_JWT_SECRET }}'

[hasura.settings]
enableRemoteSchemaPermissions = false

[functions]
[functions.node]
version = 22

[auth]
version = '0.44.2'

[auth.redirections]
clientUrl = 'http://localhost:3000'

[postgres]
version = '14.20-20251217-1'

[postgres.resources.storage]
capacity = 1

[provider]

[storage]
version = '0.9.1'

[observability]
[observability.grafana]
adminPassword = '{{ secrets.GRAFANA_ADMIN_PASSWORD }}'
`

var secretNames = []string{
	"HASURA_GRAPHQL_ADMIN_SECRET",
	"HASURA_GRAPHQL_JWT_SECRET",
	"NHOST_WEBHOOK_SECRET",
	"GRAFANA_ADMIN_PASSWORD",
	"STRIPE_SECRET_KEY",
	"UNUSED_API_TOKEN",
}

type project struct {
	dir         string
	configFile  string
	secretsFile string
	values      map[string]string // the real secret values written to disk
}

func randomValue(t *testing.T, prefix string) string {
	t.Helper()

	b := make([]byte, 20)
	if _, err := rand.Read(b); err != nil {
		t.Fatalf("rand: %v", err)
	}

	return prefix + hex.EncodeToString(b)
}

// newProject writes a project configuration and a secrets file holding fresh
// random values (long enough for any key-length rule).
func newProject(t *testing.T) *project {
	t.Helper()

	dir := t.TempDir()
	p := &project{
		dir:         dir,
		configFile:  filepath.Join(dir, "nhost.toml"),
		secretsFile: filepath.Join(dir, ".secrets"),
		values:      map[string]string{},
	}

	var sb strings.Builder
	for _, name := range secretNames {
		v := randomValue(t, "zzsv")
		p.values[name] = v
		fmt.Fprintf(&sb, "%s = '%s'\n", name, v)
	}

	if err := os.WriteFile(p.configFile, []byte(projectConfig), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}

	if err := os.WriteFile(p.secretsFile, []byte(sb.String()), 0o644); err != nil {
		t.Fatalf("write secrets: %v", err)
	}

	return p
}

// secretsOnDisk parses the secrets file as TOML (name = 'value' lines).
func (p *project) secretsOnDisk(t *testing.T) map[string]string {
	t.Helper()

	b, err := os.ReadFile(p.secretsFile)
	if err != nil {
		t.Fatalf("read secrets file: %v", err)
	}

	var raw map[string]any
	if err := toml.Unmarshal(b, &raw); err != nil {
		t.Fatalf("parse secrets file: %v\n%s", err, b)
	}

	out := make(map[string]string, len(raw))
	for k, v := range raw {
		out[k] = fmt.Sprint(v)
	}

	return out
}

func freeAddr(t *testing.T) string {
	t.Helper()

	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer l.Close()

	return l.Addr().String()
}

type server struct {
	base string
}

// startServer runs the configserver command for the project and waits until
// it answers. The server lives until the test binary exits.
func startServer(t *testing.T, p *project) *server {
	t.Helper()

	addr := freeAddr(t)
	cmd := configserver.Command()
	errc := make(chan error, 1)

	go func() {
		errc <- cmd.Run(context.Background(), []string{
			"configserver",
			"--bind", addr,
			"--storage-local-config-path", p.configFile,
			"--storage-local-secrets-path", p.secretsFile,
		})
	}()

	base := "http://" + addr
	client := &http.Client{Timeout: 2 * time.Second}
	deadline := time.Now().Add(60 * time.Second)

	for time.Now().Before(deadline) {
		select {
		case err := <-errc:
			t.Fatalf("configserver exited early: %v", err)
		default:
		}

		resp, err := client.Get(base + "/healthz")
		if err == nil {
			resp.Body.Close()

			if resp.StatusCode == http.StatusOK {
				return &server{base: base}
			}
		}

		time.Sleep(50 * time.Millisecond)
	}

	t.Fatalf("configserver did not become ready on %s", addr)

	return nil
}

type gqlResult struct {
	resp *http.Response
	body []byte
	data map[string]any
	errs []any
}

// post sends a GraphQL request the way the dashboard does (JSON body). An
// empty origin sends no Origin header.
func (s *server) post(t *testing.T, path, origin, query string, vars map[string]any) *gqlResult {
	t.Helper()

	payload, err := json.Marshal(map[string]any{"query": query, "variables": vars})
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	req, err := http.NewRequest(http.MethodPost, s.base+path, bytes.NewReader(payload))
	if err != nil {
		t.Fatalf("request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if origin != "" {
		req.Header.Set("Origin", origin)
	}

	resp, err := (&http.Client{Timeout: 20 * time.Second}).Do(req)
	if err != nil {
		t.Fatalf("POST %s: %v", path, err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	res := &gqlResult{resp: resp, body: body}

	var decoded struct {
		Data   map[string]any `json:"data"`
		Errors []any          `json:"errors"`
	}
	if json.Unmarshal(body, &decoded) == nil {
		res.data = decoded.Data
		res.errs = decoded.Errors
	}

	return res
}

// preflight sends the CORS preflight a browser sends before a JSON POST.
func (s *server) preflight(t *testing.T, path, origin string) *http.Response {
	t.Helper()

	req, err := http.NewRequest(http.MethodOptions, s.base+path, nil)
	if err != nil {
		t.Fatalf("request: %v", err)
	}

	req.Header.Set("Origin", origin)
	req.Header.Set("Access-Control-Request-Method", http.MethodPost)
	req.Header.Set("Access-Control-Request-Headers", "content-type")

	resp, err := (&http.Client{Timeout: 20 * time.Second}).Do(req)
	if err != nil {
		t.Fatalf("OPTIONS %s: %v", path, err)
	}

	_, _ = io.Copy(io.Discard, resp.Body)
	resp.Body.Close()

	return resp
}

// grantsOrigin reports whether a browser on origin may read the response.
func grantsOrigin(resp *http.Response, origin string) bool {
	for _, v := range resp.Header.Values("Access-Control-Allow-Origin") {
		v = strings.TrimSpace(v)
		if v == "*" || v == origin {
			return true
		}
	}

	return false
}

// preflightAllows reports whether a browser on origin would go on to send a
// JSON POST after this preflight answer.
func preflightAllows(resp *http.Response, origin string) bool {
	if resp.StatusCode < 200 || resp.StatusCode > 299 || !grantsOrigin(resp, origin) {
		return false
	}

	methods := strings.ToUpper(strings.Join(resp.Header.Values("Access-Control-Allow-Methods"), ","))
	if !strings.Contains(methods, "POST") && !strings.Contains(methods, "*") {
		return false
	}

	headers := strings.ToLower(strings.Join(resp.Header.Values("Access-Control-Allow-Headers"), ","))

	return strings.Contains(headers, "content-type") || strings.Contains(headers, "*")
}

// appID asks the service which application it serves (as the dashboard can).
func (s *server) appID(t *testing.T) string {
	t.Helper()

	res := s.post(t, configPath, dashboardLocal, `query { appsSecrets { appID } }`, nil)
	if res.resp.StatusCode != http.StatusOK || res.data == nil {
		t.Fatalf("appsSecrets: status %d body %s", res.resp.StatusCode, res.body)
	}

	list, _ := res.data["appsSecrets"].([]any)
	if len(list) == 0 {
		t.Fatalf("appsSecrets returned no application: %s", res.body)
	}

	id, _ := list[0].(map[string]any)["appID"].(string)
	if id == "" {
		t.Fatalf("no appID in %s", res.body)
	}

	return id
}

const appSecretsQuery = `query ($appID: uuid!) { appSecrets(appID: $appID) { name value } }`

// secretList returns name->value from an appSecrets-shaped list.
func secretList(t *testing.T, v any) map[string]string {
	t.Helper()

	out := map[string]string{}

	list, ok := v.([]any)
	if !ok {
		t.Fatalf("expected a list of secrets, got %#v", v)
	}

	for _, e := range list {
		m, _ := e.(map[string]any)
		name, _ := m["name"].(string)
		value, _ := m["value"].(string)
		out[name] = value
	}

	return out
}

func mustOK(t *testing.T, res *gqlResult, what string) {
	t.Helper()

	if res.resp.StatusCode != http.StatusOK || len(res.errs) > 0 || res.data == nil {
		t.Fatalf("%s failed: status %d body %s", what, res.resp.StatusCode, res.body)
	}
}
