package cleanup

// Shared fixtures for the cleanup-controller suites. They live in a _test.go file
// so they are compiled only when tests run, never into the product.

import (
	"context"
	"sync"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
	kyvernov2 "github.com/kyverno/kyverno/api/kyverno/v2"
	"github.com/kyverno/kyverno/pkg/clients/dclient"
	configpkg "github.com/kyverno/kyverno/pkg/config"
	"github.com/kyverno/kyverno/pkg/engine/jmespath"
	"github.com/kyverno/kyverno/pkg/toggle"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type hiddenCleanupResolver struct {
	mu    sync.Mutex
	calls []string
}

func (r *hiddenCleanupResolver) Get(ctx context.Context, namespace string, name string) (*corev1.ConfigMap, error) {
	r.mu.Lock()
	r.calls = append(r.calls, namespace+"/"+name)
	r.mu.Unlock()
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Namespace: namespace, Name: name},
		Data:       map[string]string{"value": "fixture"},
	}, nil
}

func (r *hiddenCleanupResolver) recordedCalls() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]string, len(r.calls))
	copy(out, r.calls)
	return out
}

type hiddenCleanupToggles struct{ toggle.Toggles }

func (hiddenCleanupToggles) EnableDeferredLoading() bool { return false }

func hiddenCleanupContext() context.Context {
	return toggle.NewContext(context.Background(), hiddenCleanupToggles{})
}

func hiddenCleanupController(resolver *hiddenCleanupResolver) *controller {
	return &controller{
		client:     dclient.NewEmptyFakeClient(),
		cmResolver: resolver,
		jp:         jmespath.New(configpkg.NewDefaultConfiguration(false)),
	}
}

func hiddenCleanupContextEntries(namespace string) []kyvernov1.ContextEntry {
	return []kyvernov1.ContextEntry{
		{
			Name:      "config",
			ConfigMap: &kyvernov1.ConfigMapReference{Name: "some-config", Namespace: namespace},
		},
	}
}

func hiddenNamespacedCleanupPolicy(namespace string, contextNamespace string) *kyvernov2.CleanupPolicy {
	return &kyvernov2.CleanupPolicy{
		ObjectMeta: metav1.ObjectMeta{Name: "hidden-cleanup-policy", Namespace: namespace},
		Spec:       kyvernov2.CleanupPolicySpec{Context: hiddenCleanupContextEntries(contextNamespace)},
	}
}

func hiddenClusterCleanupPolicy(contextNamespace string) *kyvernov2.ClusterCleanupPolicy {
	return &kyvernov2.ClusterCleanupPolicy{
		ObjectMeta: metav1.ObjectMeta{Name: "hidden-cluster-cleanup-policy"},
		Spec:       kyvernov2.CleanupPolicySpec{Context: hiddenCleanupContextEntries(contextNamespace)},
	}
}
