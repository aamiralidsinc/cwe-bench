package vtesting

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// The advisory's own route: a request body larger than the inspection limit,
// with the client declaring its length, is acted on while the plugin sees an
// empty body.
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

func TestSecDeclaredLengthServiceCreate(t *testing.T) {
	f := newFixture(t, true, true)
	be := &swarmBackend{}
	m := f.swarmServiceCreate(be)
	body := paddedJSON(`{"Name":"svc","TaskTemplate":{"ContainerSpec":{"Image":"busybox"}},`, 2*1024*1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/services/create", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.createCount() > 0, code)
}

func TestSecDeclaredLengthCheckpointCreate(t *testing.T) {
	f := newFixture(t, true, true)
	be := &checkpointBackend{}
	m := f.checkpointCreate(be)
	body := paddedJSON(`{"CheckpointID":"cp1",`, 2*1024*1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/containers/c1/checkpoints", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.createCount() > 0, code)
}

func paddedPrivileges(n int) string {
	head := `[{"Name":"network","Description":"","Value":["host"]},{"Name":"padding","Description":"`
	tail := `","Value":["v"]}]`
	return head + strings.Repeat("a", n-len(head)-len(tail)) + tail
}

func TestSecDeclaredLengthPluginPull(t *testing.T) {
	f := newFixture(t, true, true)
	be := &pluginBackend{}
	m := f.pluginPull(be)
	body := paddedPrivileges(2 * 1024 * 1024)
	req := httptest.NewRequest(http.MethodPost, "http://x/v1.24/plugins/pull?remote=example.com/foo/bar:latest", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	code, _ := doRequest(m, req)
	requestVisible(t, f.rec, body, be.pullCount() > 0, code)
}
