package cleanup

import (
	"testing"

	"github.com/go-logr/logr"
)

func TestFunc_CleanupNamespacedPolicyOwnNamespace(t *testing.T) {
	resolver := &hiddenCleanupResolver{}
	controller := hiddenCleanupController(resolver)
	policy := hiddenNamespacedCleanupPolicy("team-a", "team-a")

	if err := controller.cleanup(hiddenCleanupContext(), logr.Discard(), policy); err != nil {
		t.Fatalf("a cleanup policy could not read context in its own namespace: %v", err)
	}
	calls := resolver.recordedCalls()
	if len(calls) != 1 || calls[0] != "team-a/some-config" {
		t.Fatalf("unexpected config map resolution: %v", calls)
	}
}

func TestFunc_CleanupClusterPolicyCrossNamespace(t *testing.T) {
	resolver := &hiddenCleanupResolver{}
	controller := hiddenCleanupController(resolver)
	policy := hiddenClusterCleanupPolicy("other")

	if err := controller.cleanup(hiddenCleanupContext(), logr.Discard(), policy); err != nil {
		t.Fatalf("a cluster-scoped cleanup policy lost its unrestricted context access: %v", err)
	}
	calls := resolver.recordedCalls()
	if len(calls) != 1 || calls[0] != "other/some-config" {
		t.Fatalf("unexpected cross-namespace resolution: %v", calls)
	}
}
