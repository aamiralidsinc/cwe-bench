package vtesting

import (
	"strings"
	"testing"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
)

// The API-path cases. Each one drives the real context loader for a policy that
// belongs to "team-a" and must not reach anything outside it.

func hiddenAssertNoExternalRead(t *testing.T, h *hiddenHarness, err error) {
	t.Helper()
	if err == nil {
		t.Fatalf("the context entry was accepted for a namespaced policy")
	}
	if paths := h.client.recordedPaths(); len(paths) != 0 {
		t.Fatalf("the refused context entry still caused API requests: %v", paths)
	}
}

func TestSec_APICallCrossNamespace(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("cross", "/api/v1/namespaces/other/secrets/other-secret", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallDotSegment(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("dotdot", "/api/v1/namespaces/team-a/../../namespaces/other/secrets/other-secret", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallNamespacePrefixCollision(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("prefix", "/api/v1/namespaces/team-a-other/secrets/other-secret", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallClusterWideList(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("allnamespaces", "/api/v1/secrets", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallOwnNamespaceObject(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("ownnamespaceobject", "/api/v1/namespaces/team-a", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallSubstitutedNamespace(t *testing.T) {
	h := newHiddenHarness()
	if err := h.jsonContext.AddVariable("hiddenTarget", "other"); err != nil {
		t.Fatalf("cannot set the substitution fixture: %v", err)
	}
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("substituted", "/api/v1/namespaces/{{ hiddenTarget }}/secrets/other-secret", "GET"),
	})
	hiddenAssertNoExternalRead(t, h, err)
}

func TestSec_APICallWriteCrossNamespace(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("write", "/api/v1/namespaces/other/configmaps", "POST"),
	})
	hiddenAssertNoExternalRead(t, h, err)
	if strings.Contains(strings.Join(h.client.recordedPaths(), ","), "other") {
		t.Fatalf("the refused write still reached the other namespace")
	}
}
