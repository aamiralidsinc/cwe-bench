package vtesting

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	kyvernov1 "github.com/kyverno/kyverno/api/kyverno/v1"
)

func TestSec_ServiceCallDoesNotUseKyvernoCredential(t *testing.T) {
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
	err := h.load(hiddenNamespacedPolicy("team-a"), []kyvernov1.ContextEntry{
		hiddenServiceEntry("external", server.URL+"/resource"),
	})

	mu.Lock()
	defer mu.Unlock()
	for _, header := range seen {
		if strings.Contains(header, hiddenCredentialMarker) {
			t.Fatalf("Kyverno's own cluster credential was lent to a target named by a namespaced policy")
		}
	}
	_ = err // refusing the call and making it unauthenticated are both acceptable
}
