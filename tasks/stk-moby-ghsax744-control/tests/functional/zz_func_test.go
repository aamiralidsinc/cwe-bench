package vtesting

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// A normal JSON request body keeps being shown to the plugin and delivered to
// the handler unchanged.
func TestFuncSmallJsonBodyShownAndDelivered(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := `{"ListenAddr":"0.0.0.0:2377"}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	if code >= 400 {
		t.Fatalf("a legitimate JSON request was refused (status %d)", code)
	}
	seen, ok := f.rec.lastRequest()
	if !ok || string(seen.RequestBody) != body {
		t.Fatalf("the plugin did not receive the legitimate request body")
	}
	if be.initCount() != 1 {
		t.Fatalf("the handler did not run (calls %d)", be.initCount())
	}
}

// A large upload with a non-JSON body streams through untouched: it is neither
// buffered, truncated nor refused.
func TestFuncLargeNonJsonUploadUntouched(t *testing.T) {
	f := newFixture(t, true, true)
	be := &containerBackend{}
	m := f.containerArchive(be)
	payload := strings.Repeat("T", 2*1024*1024)
	req := httptest.NewRequest(http.MethodPut, "http://x/v1.24/containers/c1/archive?path=/tmp", strings.NewReader(payload))
	req.Header.Set("Content-Type", "application/x-tar")
	code, _ := doRequest(m, req)
	if code >= 400 {
		t.Fatalf("a legitimate large upload was refused (status %d)", code)
	}
	if got := be.bytesRead(); got != int64(len(payload)) {
		t.Fatalf("the handler read %d bytes of the %d-byte upload", got, len(payload))
	}
}

// Streaming responses keep reaching the client as they are produced, before the
// handler returns.
func TestFuncStreamingResponseNotWithheld(t *testing.T) {
	f := newFixture(t, true, true)
	be := &pluginBackend{}
	const first = "STREAM-CHUNK-ONE"
	const second = "STREAM-CHUNK-TWO"
	recorder := httptest.NewRecorder()
	probe := &probeWriter{ResponseWriter: recorder}
	var sawEarly bool
	be.stream = func(out io.Writer) error {
		if _, err := out.Write([]byte(first)); err != nil {
			return err
		}
		sawEarly = probe.contains(first)
		if _, err := out.Write([]byte(second)); err != nil {
			return err
		}
		return nil
	}
	m := f.pluginPull(be)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/plugins/pull?remote=example.com/foo/bar:latest", strings.NewReader(`[]`))
	req.Header.Set("Content-Type", "application/json")
	m.ServeHTTP(probe, req)
	if !strings.Contains(recorder.Body.String(), first) || !strings.Contains(recorder.Body.String(), second) {
		t.Fatalf("the streamed response did not reach the client")
	}
	if !sawEarly {
		t.Fatalf("a streamed chunk was withheld until the handler returned")
	}
}

// Credential bodies still reach the daemon on the authentication route.
func TestFuncRegistryCredentialsStillAccepted(t *testing.T) {
	const secret = "PASSWORD-MARKER-9f3a"
	f := newFixture(t, true, true)
	be := &authBackend{}
	m := f.authRoute(be)
	body := `{"username":"svc","password":"` + secret + `","serveraddress":"registry.example.com"}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/auth", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	if code >= 400 {
		t.Fatalf("the authentication request was refused (status %d)", code)
	}
	auth := be.lastAuth()
	if be.authCount() != 1 || auth.Username != "svc" || auth.Password != secret {
		t.Fatalf("the daemon did not receive the registry credentials")
	}
}

// A legitimate JSON plugin install keeps working.
func TestFuncPluginRouteLegitJson(t *testing.T) {
	f := newFixture(t, true, true)
	be := &pluginBackend{}
	m := f.pluginPull(be)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/plugins/pull?remote=example.com/foo/bar:latest", strings.NewReader(`[]`))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	if code >= 400 || be.pullCount() != 1 {
		t.Fatalf("a legitimate plugin pull was refused (status %d, calls %d)", code, be.pullCount())
	}
}

// An over-limit request must be handled (accepted or cleanly refused); it must
// not crash the daemon, and the daemon must keep serving afterwards.
func TestFuncOverLimitRequestDoesNotCrash(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := paddedJSON(`{"ListenAddr":"0.0.0.0:2377",`, 2*1024*1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	if _, _, panicked := doRequestSafe(m, req); panicked {
		t.Fatalf("an over-limit request crashed the daemon instead of being handled")
	}
	small := `{"ListenAddr":"0.0.0.0:2377"}`
	req2 := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(small))
	req2.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req2)
	if code >= 400 {
		t.Fatalf("the daemon did not keep serving after an over-limit request (status %d)", code)
	}
}

// Credential headers are never handed to plugins; other headers are.
func TestFuncCredentialHeadersNotShared(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := `{"ListenAddr":"0.0.0.0:2377"}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer SECRET-TOKEN-MARKER")
	req.Header.Set("X-Registry-Auth", "REGISTRY-AUTH-MARKER")
	code, _ := doRequest(m, req)
	if code >= 400 {
		t.Fatalf("a legitimate authenticated request was refused (status %d)", code)
	}
	seen, ok := f.rec.lastRequest()
	if !ok {
		t.Fatalf("the plugin was not consulted")
	}
	for k := range seen.RequestHeaders {
		if strings.EqualFold(k, "Authorization") || strings.EqualFold(k, "X-Registry-Auth") {
			t.Fatalf("credential header %q was shown to the plugin", k)
		}
	}
}
