package opaguard

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	opasdktest "github.com/open-policy-agent/opa/v1/sdk/test"

	"github.com/zalando/skipper/eskip"
	"github.com/zalando/skipper/filters"
	"github.com/zalando/skipper/filters/openpolicyagent"
	"github.com/zalando/skipper/filters/openpolicyagent/opaauthorizerequest"
	"github.com/zalando/skipper/filters/openpolicyagent/opaserveresponse"
	"github.com/zalando/skipper/proxy"
	"github.com/zalando/skipper/routing"
	"github.com/zalando/skipper/routing/testdataclient"
)

// Policies the behavioural suites evaluate. They are part of the test, not the
// product: the product only has to make the completeness signal available.
// oversizedPrefix is larger than the leading body prefix a prefix-evaluating
// route hands to the policy.
const oversizedPrefix = 40 * 1024

const (
	PolicyDenyTruncated = `
package envoy.authz

import rego.v1

default allow := false

allow if {
	input.truncated_body == false
}
`

	PolicyAllowAll = `
package envoy.authz

import rego.v1

default allow := true
`

	PolicyServeResponse = `
package envoy.authz

import rego.v1

default allow := {"allowed": false}

allow := {"allowed": true, "http_status": 200, "body": "served"} if {
	input.truncated_body == false
}
`
)

// StartRegistry starts an in-process OPA control plane serving one bundle and
// returns a registry bound to it. Everything runs on loopback.
func StartRegistry(t *testing.T, policy string, maxBodyBytes, readBufferBytes int64) (*openpolicyagent.OpenPolicyAgentRegistry, string) {
	t.Helper()

	const bundleName = "guard-bundle"
	controlPlane := opasdktest.MustNewServer(
		opasdktest.MockBundle("/bundles/"+bundleName, map[string]string{
			"main.rego": policy,
		}),
	)
	t.Cleanup(controlPlane.Stop)

	config := fmt.Appendf(nil, `{
		"services": {"test": {"url": %q}},
		"bundles": {"test": {"resource": "/bundles/{{ .bundlename }}"}},
		"labels": {"environment": "test"},
		"plugins": {"envoy_ext_authz_grpc": {"path": "envoy/authz/allow", "dry-run": false}}
	}`, controlPlane.URL())

	registry, err := openpolicyagent.NewOpenPolicyAgentRegistry(
		openpolicyagent.WithPreloadingEnabled(true),
		openpolicyagent.WithEnableDataPreProcessingOptimization(true),
		openpolicyagent.WithInstanceStartupTimeout(10*time.Second),
		openpolicyagent.WithMaxRequestBodyBytes(maxBodyBytes),
		openpolicyagent.WithReadBodyBufferSize(readBufferBytes),
		openpolicyagent.WithOpenPolicyAgentInstanceConfig(openpolicyagent.WithConfigTemplate(config)),
	)
	if err != nil {
		t.Fatalf("start OPA registry: %v", err)
	}
	t.Cleanup(registry.Close)

	return registry, bundleName
}

// Recorder is the upstream behind a route. It records every request that
// actually reached it, which is how the suites prove that a refused request
// had no effect.
type Recorder struct {
	mu     sync.Mutex
	hits   int
	bodies []string
}

func (r *Recorder) record(body string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.hits++
	r.bodies = append(r.bodies, body)
}

func (r *Recorder) Hits() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.hits
}

func (r *Recorder) Bodies() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]string, len(r.bodies))
	copy(out, r.bodies)
	return out
}

// StartRoute wires one eskip route whose only filter is filterName(bundle) and
// returns the proxy URL and the upstream recorder.
func StartRoute(t *testing.T, registry *openpolicyagent.OpenPolicyAgentRegistry, filterName, bundleName string) (string, *Recorder) {
	t.Helper()

	recorder := &Recorder{}
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		recorder.record(string(body))
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("upstream"))
	}))
	t.Cleanup(upstream.Close)

	filterRegistry := make(filters.Registry)
	filterRegistry.Register(opaauthorizerequest.NewOpaAuthorizeRequestSpec(registry))
	filterRegistry.Register(opaauthorizerequest.NewOpaAuthorizeRequestWithBodySpec(registry))
	filterRegistry.Register(opaauthorizerequest.NewOpaAuthorizeRequestBodyPrefixSpec(registry))
	filterRegistry.Register(opaserveresponse.NewOpaServeResponseSpec(registry))
	filterRegistry.Register(opaserveresponse.NewOpaServeResponseWithReqBodySpec(registry))

	route := eskip.MustParse(fmt.Sprintf(`r1: * -> %s("%s") -> "%s";`, filterName, bundleName, upstream.URL))
	dc := testdataclient.New(route)
	t.Cleanup(dc.Close)

	router := routing.New(routing.Options{
		FilterRegistry:  filterRegistry,
		DataClients:     []routing.DataClient{dc},
		PreProcessors:   []routing.PreProcessor{registry.NewPreProcessor()},
		PostProcessors:  []routing.PostProcessor{registry},
		PollTimeout:     time.Second,
		SignalFirstLoad: true,
	})
	t.Cleanup(router.Close)
	<-router.FirstLoad()

	p := proxy.WithParams(proxy.Params{Routing: router})
	t.Cleanup(func() { p.Close() })
	front := httptest.NewServer(p)
	t.Cleanup(front.Close)

	return front.URL, recorder
}

// Post sends a POST request. When chunked is true the body has no declared
// length, so the proxy sees it the way it sees a streamed or HTTP/2 upload.
func Post(t *testing.T, url, contentType string, body string, chunked bool, extraHeaders map[string]string) *http.Response {
	t.Helper()

	var reader io.Reader
	if chunked {
		reader = io.NopCloser(strings.NewReader(body))
	} else {
		reader = strings.NewReader(body)
	}

	req, err := http.NewRequest(http.MethodPost, url+"/upload", reader)
	if err != nil {
		t.Fatalf("build request: %v", err)
	}
	req.Header.Set("Content-Type", contentType)
	for k, v := range extraHeaders {
		req.Header.Set(k, v)
	}
	if chunked {
		req.ContentLength = -1
		req.TransferEncoding = []string{"chunked"}
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("send request: %v", err)
	}
	t.Cleanup(func() { resp.Body.Close() })
	return resp
}

// FormBody returns a form-encoded body of exactly size bytes. Every encoding
// used by the suites has to parse successfully even when it is cut, so the
// policy decision depends only on the completeness signal.
func FormBody(size int) string {
	if size < 2 {
		size = 2
	}
	return "a=" + strings.Repeat("A", size-2)
}
