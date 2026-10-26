// Package vtesting holds the hidden behavioural checks for the daemon's
// authorization-plugin boundary. It is staged into the product tree at grading
// time; every case drives a real HTTP route through the real authorization
// middleware and observes what a plugin is actually handed.
package vtesting

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	"github.com/docker/distribution/reference"
	"github.com/docker/docker/api/server/httputils"
	"github.com/docker/docker/api/server/router"
	checkpointrouter "github.com/docker/docker/api/server/router/checkpoint"
	containerrouter "github.com/docker/docker/api/server/router/container"
	pluginrouter "github.com/docker/docker/api/server/router/plugin"
	swarmrouter "github.com/docker/docker/api/server/router/swarm"
	"github.com/docker/docker/api/types"
	swarmtypes "github.com/docker/docker/api/types/swarm"
	"github.com/docker/docker/pkg/authorization"
	"github.com/docker/docker/pkg/plugingetter"
	"github.com/docker/docker/pkg/plugins"
	dockerplugin "github.com/docker/docker/plugin"
	"github.com/gorilla/mux"
)

const (
	versionMatcher = "/v{version:[0-9.]+}"
	apiVersion     = "1.24"
	pluginName     = "test-authz"
)

// ---------------------------------------------------------------------------
// A plugin that records every authorization call and answers allow or deny.
// ---------------------------------------------------------------------------

type pluginRecorder struct {
	mu            sync.Mutex
	requests      []authorization.Request
	responses     []authorization.Request
	allowRequest  bool
	allowResponse bool
}

func (p *pluginRecorder) serveHTTP(w http.ResponseWriter, r *http.Request) {
	var req authorization.Request
	_ = json.NewDecoder(r.Body).Decode(&req)
	p.mu.Lock()
	switch r.URL.Path {
	case "/" + authorization.AuthZApiRequest:
		p.requests = append(p.requests, req)
	case "/" + authorization.AuthZApiResponse:
		p.responses = append(p.responses, req)
	}
	allow := p.allowRequest
	if r.URL.Path == "/"+authorization.AuthZApiResponse {
		allow = p.allowResponse
	}
	p.mu.Unlock()
	_ = json.NewEncoder(w).Encode(&authorization.Response{Allow: allow, Msg: "recorded"})
}

func (p *pluginRecorder) lastRequest() (authorization.Request, bool) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.requests) == 0 {
		return authorization.Request{}, false
	}
	return p.requests[len(p.requests)-1], true
}

func (p *pluginRecorder) lastResponse() (authorization.Request, bool) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.responses) == 0 {
		return authorization.Request{}, false
	}
	return p.responses[len(p.responses)-1], true
}

type fakeCompat struct {
	name   string
	client *plugins.Client
}

func (f *fakeCompat) Name() string               { return f.name }
func (f *fakeCompat) ScopedPath(s string) string { return s }
func (f *fakeCompat) IsV1() bool                 { return true }
func (f *fakeCompat) Client() *plugins.Client    { return f.client }

type fakeGetter struct{ p *fakeCompat }

func (g *fakeGetter) Get(name, capability string, mode int) (plugingetter.CompatPlugin, error) {
	return g.p, nil
}
func (g *fakeGetter) GetAllByCap(capability string) ([]plugingetter.CompatPlugin, error) {
	return nil, nil
}
func (g *fakeGetter) GetAllManagedPluginsByCap(capability string) []plugingetter.CompatPlugin {
	return nil
}
func (g *fakeGetter) Handle(capability string, callback func(string, *plugins.Client)) {}

// ---------------------------------------------------------------------------
// Fixture: the real authorization middleware in front of a real route table.
// ---------------------------------------------------------------------------

type fixture struct {
	t      *testing.T
	mw     *authorization.Middleware
	rec    *pluginRecorder
	server *httptest.Server
}

func newFixture(t *testing.T, allowRequest, allowResponse bool) *fixture {
	t.Helper()
	rec := &pluginRecorder{allowRequest: allowRequest, allowResponse: allowResponse}
	srv := httptest.NewServer(http.HandlerFunc(rec.serveHTTP))
	client, err := plugins.NewClient(srv.URL, nil)
	if err != nil {
		srv.Close()
		t.Fatalf("cannot build the plugin client: %v", err)
	}
	getter := &fakeGetter{p: &fakeCompat{name: pluginName, client: client}}
	authorization.SetPluginGetter(getter)
	mw := authorization.NewMiddleware([]string{pluginName}, getter)
	f := &fixture{t: t, mw: mw, rec: rec, server: srv}
	t.Cleanup(srv.Close)
	return f
}

// mount registers the selected routes the way the daemon does (versioned and
// unversioned paths) and wraps each in the authorization middleware plus the
// daemon's own error mapping.
func (f *fixture) mount(routes []router.Route, enableExperimental bool) *mux.Router {
	m := mux.NewRouter()
	for _, route := range routes {
		rt := route
		if enableExperimental {
			if er, ok := rt.(router.ExperimentalRoute); ok {
				er.Enable()
			}
		}
		wrapped := f.mw.WrapHandler(rt.Handler())
		h := func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(context.Background(), httputils.APIVersionKey, apiVersion)
			if err := wrapped(ctx, w, r, mux.Vars(r)); err != nil {
				httputils.MakeErrorHandler(err)(w, r)
			}
		}
		m.Path(versionMatcher + rt.Path()).Methods(rt.Method()).HandlerFunc(h)
		m.Path(rt.Path()).Methods(rt.Method()).HandlerFunc(h)
	}
	return m
}

func pickRoute(all []router.Route, method, path string) []router.Route {
	for _, r := range all {
		if r.Method() == method && r.Path() == path {
			return []router.Route{r}
		}
	}
	return nil
}

func (f *fixture) swarmInit(be *swarmBackend) *mux.Router {
	return f.mount(pickRoute(swarmrouter.NewRouter(be).Routes(), http.MethodPost, "/swarm/init"), false)
}
func (f *fixture) swarmServiceCreate(be *swarmBackend) *mux.Router {
	return f.mount(pickRoute(swarmrouter.NewRouter(be).Routes(), http.MethodPost, "/services/create"), false)
}
func (f *fixture) checkpointCreate(be *checkpointBackend) *mux.Router {
	return f.mount(pickRoute(checkpointrouter.NewRouter(be, nil).Routes(), http.MethodPost, "/containers/{name:.*}/checkpoints"), true)
}
func (f *fixture) pluginPull(be *pluginBackend) *mux.Router {
	return f.mount(pickRoute(pluginrouter.NewRouter(be).Routes(), http.MethodPost, "/plugins/pull"), false)
}
func (f *fixture) containerArchive(be *containerBackend) *mux.Router {
	return f.mount(pickRoute(containerrouter.NewRouter(be, nil).Routes(), http.MethodPut, "/containers/{name:.*}/archive"), false)
}
// authRoute drives the authentication endpoint shape through the real
// middleware. The daemon-side action is represented by a recording backend so
// the case observes exactly what a plugin is handed and what the daemon does.
func (f *fixture) authRoute(be *authBackend) *mux.Router {
	h := func(ctx context.Context, w http.ResponseWriter, r *http.Request, vars map[string]string) error {
		var cfg types.AuthConfig
		if err := json.NewDecoder(r.Body).Decode(&cfg); err != nil {
			return err
		}
		be.authenticate(cfg)
		return httputils.WriteJSON(w, http.StatusOK, map[string]string{"Status": "Login Succeeded", "IdentityToken": "token"})
	}
	return f.mount([]router.Route{router.NewPostRoute("/auth", h)}, false)
}

// ---------------------------------------------------------------------------
// Product backends: embedded interfaces, with only the driven method real.
// ---------------------------------------------------------------------------

type swarmBackend struct {
	swarmrouter.Backend
	mu      sync.Mutex
	inits   []swarmtypes.InitRequest
	creates []swarmtypes.ServiceSpec
}

func (b *swarmBackend) Init(req swarmtypes.InitRequest) (string, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.inits = append(b.inits, req)
	return "node-id", nil
}

func (b *swarmBackend) CreateService(spec swarmtypes.ServiceSpec, encodedAuth string, queryRegistry bool) (*types.ServiceCreateResponse, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.creates = append(b.creates, spec)
	return &types.ServiceCreateResponse{ID: "service-id"}, nil
}

func (b *swarmBackend) initCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.inits)
}

func (b *swarmBackend) createCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.creates)
}

type checkpointBackend struct {
	checkpointrouter.Backend
	mu      sync.Mutex
	created []string
}

func (b *checkpointBackend) CheckpointCreate(container string, config types.CheckpointCreateOptions) error {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.created = append(b.created, container)
	return nil
}

func (b *checkpointBackend) createCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.created)
}

type pluginBackend struct {
	pluginrouter.Backend
	mu     sync.Mutex
	pulls  []string
	stream func(io.Writer) error
}

func (b *pluginBackend) Pull(ctx context.Context, ref reference.Named, name string, metaHeaders http.Header, authConfig *types.AuthConfig, privileges types.PluginPrivileges, outStream io.Writer, opts ...dockerplugin.CreateOpt) error {
	b.mu.Lock()
	b.pulls = append(b.pulls, name)
	stream := b.stream
	b.mu.Unlock()
	if stream != nil {
		return stream(outStream)
	}
	return nil
}

func (b *pluginBackend) pullCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.pulls)
}

type containerBackend struct {
	containerrouter.Backend
	mu   sync.Mutex
	read int64
}

func (b *containerBackend) ContainerExtractToDir(name, path string, copyUIDGID, noOverwriteDirNonDir bool, content io.Reader) error {
	n, err := io.Copy(io.Discard, content)
	b.mu.Lock()
	b.read = n
	b.mu.Unlock()
	return err
}

func (b *containerBackend) bytesRead() int64 {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.read
}

type authBackend struct {
	mu    sync.Mutex
	auths []types.AuthConfig
}

func (b *authBackend) authenticate(cfg types.AuthConfig) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.auths = append(b.auths, cfg)
}

func (b *authBackend) authCount() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.auths)
}

func (b *authBackend) lastAuth() types.AuthConfig {
	b.mu.Lock()
	defer b.mu.Unlock()
	if len(b.auths) == 0 {
		return types.AuthConfig{}
	}
	return b.auths[len(b.auths)-1]
}

// ---------------------------------------------------------------------------
// Request/response helpers.
// ---------------------------------------------------------------------------

// paddedJSON returns a valid JSON object of exactly n bytes whose first key
// holds prefix; an unknown padding field fills the rest.
func paddedJSON(prefix string, n int) string {
	head := prefix + `"Padding":"`
	tail := `"}`
	fill := n - len(head) - len(tail)
	if fill < 0 {
		fill = 0
	}
	return head + strings.Repeat("a", fill) + tail
}

func doRequest(m http.Handler, req *http.Request) (code int, body string) {
	w := httptest.NewRecorder()
	m.ServeHTTP(w, req)
	return w.Code, w.Body.String()
}

func doRequestSafe(m http.Handler, req *http.Request) (code int, body string, panicked bool) {
	defer func() {
		if recover() != nil {
			panicked = true
		}
	}()
	code, body = doRequest(m, req)
	return code, body, false
}

// requestVisible asserts the invariant: the plugin saw the exact body the
// daemon acted on, or the request was refused without effect.
func requestVisible(t *testing.T, rec *pluginRecorder, want string, acted bool, code int) {
	t.Helper()
	seen, ok := rec.lastRequest()
	if ok && string(seen.RequestBody) == want {
		return
	}
	if acted {
		t.Fatalf("the daemon acted on a request whose real body was not shown to the plugin "+
			"(plugin saw %d bytes of %d)", len(seen.RequestBody), len(want))
	}
	if code < 400 {
		t.Fatalf("a request whose body was not shown to the plugin was neither acted on nor refused (status %d)", code)
	}
}

// probeWriter records everything written to the client and whether a marker
// became visible before the handler returned.
type probeWriter struct {
	http.ResponseWriter
	mu  sync.Mutex
	got strings.Builder
}

func (p *probeWriter) Write(b []byte) (int, error) {
	p.mu.Lock()
	p.got.Write(b)
	p.mu.Unlock()
	return p.ResponseWriter.Write(b)
}

func (p *probeWriter) Flush() {
	if f, ok := p.ResponseWriter.(http.Flusher); ok {
		f.Flush()
	}
}

func (p *probeWriter) CloseNotify() <-chan bool { return nil }

func (p *probeWriter) contains(s string) bool {
	p.mu.Lock()
	defer p.mu.Unlock()
	return strings.Contains(p.got.String(), s)
}
