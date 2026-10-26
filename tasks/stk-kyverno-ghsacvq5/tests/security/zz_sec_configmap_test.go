package vtesting

import (
	"strings"
	"testing"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
)

func TestSec_ConfigMapCrossNamespace(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenConfigMapEntry("cross", "other", "other-config"),
	})
	if err == nil {
		t.Fatalf("a config map outside the policy namespace was accepted")
	}
	for _, call := range h.resolver.recordedCalls() {
		if !strings.HasPrefix(call, "team-a/") {
			t.Fatalf("the refused context entry still resolved %q", call)
		}
	}
}

func TestSec_ConfigMapEmptySubstitutedNamespace(t *testing.T) {
	h := newHiddenHarness()
	if err := h.jsonContext.AddVariable("hiddenTeam", ""); err != nil {
		t.Fatalf("cannot set the substitution fixture: %v", err)
	}
	_ = h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenConfigMapEntry("empty", "{{ hiddenTeam }}", "some-config"),
	})
	for _, call := range h.resolver.recordedCalls() {
		if !strings.HasPrefix(call, "team-a/") {
			t.Fatalf("an empty target namespace resolved outside the policy namespace: %q", call)
		}
	}
}
