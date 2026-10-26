package vtesting

// Shared harness for the behavioural suites. Everything here is test bookkeeping:
// a recording client, a recording ConfigMap resolver, policy fixtures and the
// credential fixture the service-call tests need.

import (
	"context"
	"io"
	"os"
	"sync"
	"testing"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
	"github.com/kyverno/kyverno/pkg/config"
	engineapi "github.com/kyverno/kyverno/pkg/engine/api"
	enginecontext "github.com/kyverno/kyverno/pkg/engine/context"
	"github.com/kyverno/kyverno/pkg/engine/factories"
	"github.com/kyverno/kyverno/pkg/engine/jmespath"
	"github.com/kyverno/kyverno/pkg/toggle"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// hiddenCredentialPath and hiddenCredentialMarker are the fixture for the tests
// that observe whether Kyverno lends its own cluster identity.
const (
	hiddenCredentialPath   = "/var/run/secrets/kubernetes.io/serviceaccount/token"
	hiddenCredentialMarker = "hidden-kyverno-cluster-credential"
)

type hiddenToggles struct{ toggle.Toggles }

func (hiddenToggles) EnableDeferredLoading() bool { return false }

func hiddenBaseContext() context.Context {
	return toggle.NewContext(context.Background(), hiddenToggles{})
}

func hiddenInstallCredential(t *testing.T) {
	t.Helper()
	_ = os.Remove(hiddenCredentialPath)
	if err := os.WriteFile(hiddenCredentialPath, []byte(hiddenCredentialMarker), 0o600); err != nil {
		t.Fatalf("cannot install the credential fixture at %s: %v", hiddenCredentialPath, err)
	}
	t.Cleanup(func() { _ = os.Remove(hiddenCredentialPath) })
}

type hiddenRawClient struct {
	mu    sync.Mutex
	paths []string
}

func (c *hiddenRawClient) RawAbsPath(ctx context.Context, path string, method string, dataReader io.Reader) ([]byte, error) {
	c.mu.Lock()
	c.paths = append(c.paths, method+" "+path)
	c.mu.Unlock()
	return []byte(`{"kind":"List","items":[]}`), nil
}

func (c *hiddenRawClient) recordedPaths() []string {
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make([]string, len(c.paths))
	copy(out, c.paths)
	return out
}

type hiddenConfigMapResolver struct {
	mu    sync.Mutex
	calls []string
}

func (r *hiddenConfigMapResolver) Get(ctx context.Context, namespace string, name string) (*corev1.ConfigMap, error) {
	r.mu.Lock()
	r.calls = append(r.calls, namespace+"/"+name)
	r.mu.Unlock()
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Namespace: namespace, Name: name},
		Data:       map[string]string{"value": "fixture"},
	}, nil
}

func (r *hiddenConfigMapResolver) recordedCalls() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]string, len(r.calls))
	copy(out, r.calls)
	return out
}

type hiddenHarness struct {
	jp          jmespath.Interface
	jsonContext enginecontext.Interface
	client      *hiddenRawClient
	resolver    *hiddenConfigMapResolver
}

func newHiddenHarness() *hiddenHarness {
	jp := jmespath.New(config.NewDefaultConfiguration(false))
	return &hiddenHarness{
		jp:          jp,
		jsonContext: enginecontext.NewContext(jp),
		client:      &hiddenRawClient{},
		resolver:    &hiddenConfigMapResolver{},
	}
}

// load drives the product's own context-loading entry point: build the loader the
// engine builds for a policy, then load the declared context entries into a fresh
// JSON context.
func (h *hiddenHarness) load(policy kyvernov1.PolicyInterface, entries []kyvernov1.ContextEntry) error {
	factory := factories.DefaultContextLoaderFactory(h.resolver)
	loader := factory(policy, kyvernov1.Rule{})
	return loader.Load(hiddenBaseContext(), h.jp, engineapi.RawClient(h.client), nil, entries, h.jsonContext)
}

func hiddenNamespacedPolicy(namespace string) kyvernov1.PolicyInterface {
	return &kyvernov1.Policy{ObjectMeta: metav1.ObjectMeta{Name: "hidden-policy", Namespace: namespace}}
}

func hiddenClusterPolicy() kyvernov1.PolicyInterface {
	return &kyvernov1.ClusterPolicy{ObjectMeta: metav1.ObjectMeta{Name: "hidden-cluster-policy"}}
}

func hiddenAPICallEntry(name string, urlPath string, method kyvernov1.Method) kyvernov1.ContextEntry {
	return kyvernov1.ContextEntry{
		Name: name,
		APICall: &kyvernov1.ContextAPICall{
			APICall: kyvernov1.APICall{URLPath: urlPath, Method: method},
		},
	}
}

func hiddenServiceEntry(name string, url string, headers ...kyvernov1.HTTPHeader) kyvernov1.ContextEntry {
	return kyvernov1.ContextEntry{
		Name: name,
		APICall: &kyvernov1.ContextAPICall{
			APICall: kyvernov1.APICall{
				Method:  "GET",
				Service: &kyvernov1.ServiceCall{URL: url, Headers: headers},
			},
		},
	}
}

func hiddenConfigMapEntry(name string, namespace string, configMap string) kyvernov1.ContextEntry {
	return kyvernov1.ContextEntry{
		Name:      name,
		ConfigMap: &kyvernov1.ConfigMapReference{Name: configMap, Namespace: namespace},
	}
}
