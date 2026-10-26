package vtesting

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
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

func TestFunc_NamespacedPolicyOwnNamespaceConfigMap(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenConfigMapEntry("own", "team-a", "team-config"),
	})
	if err != nil {
		t.Fatalf("a namespaced policy could not read a config map in its own namespace: %v", err)
	}
	calls := h.resolver.recordedCalls()
	if len(calls) != 1 || calls[0] != "team-a/team-config" {
		t.Fatalf("unexpected config map resolution: %v", calls)
	}
}

func TestFunc_ClusterPolicyDefaultNamespaceConfigMap(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenClusterPolicy(), []kyvernov1.ContextEntry{
		hiddenConfigMapEntry("defaulted", "", "cluster-config"),
	})
	if err != nil {
		t.Fatalf("a cluster-scoped policy lost the existing default-namespace behaviour: %v", err)
	}
	calls := h.resolver.recordedCalls()
	if len(calls) != 1 || calls[0] != "default/cluster-config" {
		t.Fatalf("unexpected default-namespace resolution: %v", calls)
	}
}

func TestFunc_ClusterPolicyCrossNamespaceConfigMap(t *testing.T) {
	h := newHiddenHarness()
	err := h.load(hiddenClusterPolicy(), []kyvernov1.ContextEntry{
		hiddenConfigMapEntry("cross", "other", "other-config"),
	})
	if err != nil {
		t.Fatalf("a cluster-scoped policy lost its unrestricted config map access: %v", err)
	}
	calls := h.resolver.recordedCalls()
	if len(calls) != 1 || calls[0] != "other/other-config" {
		t.Fatalf("unexpected cross-namespace resolution: %v", calls)
	}
}

func TestFunc_NamespacedPolicyExternalCallStillWorks(t *testing.T) {
	hiddenInstallCredential(t)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenServiceEntry("external", server.URL+"/resource"),
	})
	if err != nil {
		t.Fatalf("a legitimate external call from a namespaced policy was refused: %v", err)
	}
	value, err := h.jsonContext.Query("external")
	if err != nil || value == nil {
		t.Fatalf("the external call result was not stored: value=%v err=%v", value, err)
	}
}

func TestFunc_NamespacedPolicySuppliedCredentialPreserved(t *testing.T) {
	var mu sync.Mutex
	var seen []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		seen = append(seen, r.Header.Get("Authorization"))
		mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	h := newHiddenHarness()
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenServiceEntry("external", server.URL+"/resource", kyvernov1.HTTPHeader{Key: "Authorization", Value: "Bearer policy-supplied"}),
	})
	if err != nil {
		t.Fatalf("a namespaced policy could not use its own credential: %v", err)
	}
	mu.Lock()
	defer mu.Unlock()
	if len(seen) != 1 || seen[0] != "Bearer policy-supplied" {
		t.Fatalf("the policy-supplied credential was not preserved: %v", seen)
	}
}

func TestFunc_ClusterPolicyServiceUsesKyvernoCredential(t *testing.T) {
	hiddenInstallCredential(t)
	var mu sync.Mutex
	var seen []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		seen = append(seen, r.Header.Get("Authorization"))
		mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	h := newHiddenHarness()
	err := h.load(hiddenClusterPolicy(), []kyvernov1.ContextEntry{
		hiddenServiceEntry("external", server.URL+"/resource"),
	})
	if err != nil {
		t.Fatalf("a cluster-scoped external call failed: %v", err)
	}
	mu.Lock()
	defer mu.Unlock()
	if len(seen) != 1 || seen[0] != "Bearer "+hiddenCredentialMarker {
		t.Fatalf("a cluster-scoped policy stopped using Kyverno's own identity: %v", seen)
	}
}
