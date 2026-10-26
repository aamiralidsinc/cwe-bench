package vtesting

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/docker/docker/api/server/router"
)

// T1: a body whose length the client declares must not be hidden from the
// plugin while the daemon acts on it.
func TestSecDeclaredLengthBodyNotHidden(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := paddedJSON(`{"ListenAddr":"0.0.0.0:2377",`, 2*1024*1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.initCount() > 0, code)
}

// T2: the same operation reached with a streamed (undeclared-length) body.
func TestSecStreamedLengthBodyNotHidden(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := paddedJSON(`{"ListenAddr":"0.0.0.0:2377",`, 2*1024*1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.ContentLength = -1
	req.TransferEncoding = []string{"chunked"}
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.initCount() > 0, code)
}

// T3: a JSON body on a JSON-parsing route is acted on whatever media type the
// client declares.
func TestSecSwarmRouteBodyNotHiddenByMediaType(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmInit(be)
	body := `{"ListenAddr":"0.0.0.0:2377"}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/swarm/init", strings.NewReader(body))
	req.Header.Set("Content-Type", "text/plain")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.initCount() > 0, code)
}

func TestSecServiceRouteBodyNotHiddenByMediaType(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmServiceCreate(be)
	body := `{"Name":"svc","TaskTemplate":{"ContainerSpec":{"Image":"busybox"}}}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/services/create", strings.NewReader(body))
	req.Header.Set("Content-Type", "text/plain")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.createCount() > 0, code)
}

func TestSecPluginRouteBodyNotHiddenByMediaType(t *testing.T) {
	f := newFixture(t, true, true)
	be := &pluginBackend{}
	m := f.pluginPull(be)
	body := `[]`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/plugins/pull?remote=example.com/foo/bar:latest", strings.NewReader(body))
	req.Header.Set("Content-Type", "text/plain")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.pullCount() > 0, code)
}

func TestSecCheckpointRouteBodyNotHiddenByMediaType(t *testing.T) {
	f := newFixture(t, true, true)
	be := &checkpointBackend{}
	m := f.checkpointCreate(be)
	body := `{"CheckpointID":"cp1","CheckpointDir":"/tmp/checkpoints"}`
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/containers/c1/checkpoints", strings.NewReader(body))
	req.Header.Set("Content-Type", "text/plain")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.createCount() > 0, code)
}

// T4: a denied response must not be partially delivered first.
func TestSecResponseDecisionBeforeDelivery(t *testing.T) {
	f := newFixture(t, true, false) // the plugin denies every response
	const marker = "PRIVILEGED-RESPONSE-MARKER"
	chunk := []byte(strings.Repeat(marker+"|", (100*1024)/(len(marker)+1)))
	h := func(ctx context.Context, w http.ResponseWriter, r *http.Request, vars map[string]string) error {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(chunk)
		_, _ = w.Write(chunk)
		return nil
	}
	m := f.mount([]router.Route{router.NewGetRoute("/containers/json", h)}, false)
	code, body := doRequest(m, httptest.NewRequest(http.MethodGet, "http://x/v1.24/containers/json", nil))
	if strings.Contains(body, marker) {
		t.Fatalf("the plugin denied the response but %d bytes of its content had already reached the client", len(body))
	}
	if code < 400 {
		t.Fatalf("a denied response was delivered as success (status %d)", code)
	}
}

// T6: the credential body a client sends to authenticate must not be shown to
// the plugin, on any path shape that reaches the authentication route.
func TestSecRegistryCredentialBodyNotShared(t *testing.T) {
	const secret = "PASSWORD-MARKER-9f3a"
	for _, path := range []string{"/v1.24/auth", "/auth"} {
		f := newFixture(t, true, true)
		be := &authBackend{}
		m := f.authRoute(be)
		body := `{"username":"svc","password":"` + secret + `","serveraddress":"registry.example.com"}`
		req := httptest.NewRequest(http.MethodPost, "http://x"+path, strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		code, _ := doRequest(m, req)
		seen, _ := f.rec.lastRequest()
		if strings.Contains(string(seen.RequestBody), secret) {
			t.Fatalf("registry credential material was shown to the plugin for %s", path)
		}
		if code >= 400 || be.authCount() != 1 {
			t.Fatalf("the authentication request was not handled for %s (status %d, backend calls %d)", path, code, be.authCount())
		}
	}
}
