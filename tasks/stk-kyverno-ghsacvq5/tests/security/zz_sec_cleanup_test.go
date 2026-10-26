package cleanup

import (
	"testing"

	"github.com/go-logr/logr"
)

func TestSec_CleanupContextCrossNamespace(t *testing.T) {
	resolver := &hiddenCleanupResolver{}
	controller := hiddenCleanupController(resolver)
	// The declared target has no namespace of its own: it must be resolved inside the
	// cleanup policy's namespace, never outside it.
	policy := hiddenNamespacedCleanupPolicy("team-a", "")

	_ = controller.cleanup(hiddenCleanupContext(), logr.Discard(), policy)
	for _, call := range resolver.recordedCalls() {
		if call != "team-a/some-config" {
			t.Fatalf("the refused context entry still resolved %q", call)
		}
	}
}
