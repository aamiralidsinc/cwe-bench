package vtesting

import (
	"strings"
	"testing"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
)

func TestFunc_NamespacedPolicyOwnNamespaceAPICall(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("own", "/api/v1/namespaces/team-a/configmaps", "GET"),
	})
	if err != nil {
		t.Fatalf("a namespaced policy could not read its own namespace: %v", err)
	}
	paths := h.client.recordedPaths()
	if len(paths) != 1 || !strings.Contains(paths[0], "/namespaces/team-a/") {
		t.Fatalf("the own-namespace request was not made as expected: %v", paths)
	}
}

func TestFunc_NamespacedPolicyOwnNamespaceResource(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("ownnamespace", "/apis/apps/v1/namespaces/team-a/deployments", "GET"),
	})
	if err != nil {
		t.Fatalf("a namespaced policy could not read a resource in its own namespace: %v", err)
	}
	paths := h.client.recordedPaths()
	if len(paths) != 1 || !strings.Contains(paths[0], "/namespaces/team-a/") {
		t.Fatalf("the own-namespace resource request was not made as expected: %v", paths)
	}
}

func TestFunc_NamespacedPolicySubstitutedOwnNamespaceAPICall(t *testing.T) {
	h := newHiddenHarness()
	if err := h.jsonContext.AddVariable("hiddenTarget", "team-a"); err != nil {
		t.Fatalf("cannot set the substitution fixture: %v", err)
	}
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("substituted", "/api/v1/namespaces/{{ hiddenTarget }}/configmaps", "GET"),
	})
	if err != nil {
		t.Fatalf("a namespaced policy could not use a variable resolving to its own namespace: %v", err)
	}
	paths := h.client.recordedPaths()
	if len(paths) != 1 || !strings.Contains(paths[0], "/namespaces/team-a/") {
		t.Fatalf("the substituted own-namespace request was not made as expected: %v", paths)
	}
}

func TestFunc_ClusterPolicyUnrestrictedAPICall(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenClusterPolicy(), []kyvernov1.ContextEntry{
		hiddenAPICallEntry("cluster", "/api/v1/namespaces/other/secrets/other-secret", "GET"),
	})
	if err != nil {
		t.Fatalf("a cluster-scoped policy lost its unrestricted access: %v", err)
	}
	if paths := h.client.recordedPaths(); len(paths) != 1 {
		t.Fatalf("the cluster-scoped request was not made: %v", paths)
	}
}
