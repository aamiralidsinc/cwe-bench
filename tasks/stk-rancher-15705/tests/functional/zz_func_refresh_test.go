package providerrefresh

import (
	"fmt"
	"testing"

	apiv3 "github.com/rancher/rancher/pkg/apis/management.cattle.io/v3"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// A transient provider failure keeps the user signed in.
func TestFunc_RefreshErrorKeepsUserLoggedIn(t *testing.T) {
	r, attribs, deleteCalled := zzRefreshFixture(t, &zzRefreshProvider{err: fmt.Errorf("connection refused")})
	got, err := r.refreshAttributes(attribs)
	if err != nil {
		t.Fatalf("a transient provider error must not fail the refresh: %v", err)
	}
	if got == nil {
		t.Fatal("refresh returned no attribute")
	}
	if *deleteCalled {
		t.Fatal("a transient provider error deleted the user's login token")
	}
}

// A refresh that succeeds stores exactly the teams the provider currently confirms.
func TestFunc_SuccessfulRefreshStoresCurrentTeams(t *testing.T) {
	current := apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_team://34567"},
		LoginName:     "dev-team",
		Provider:      "githubapp",
		PrincipalType: "group",
	}
	r, attribs, _ := zzRefreshFixture(t, &zzRefreshProvider{groups: []apiv3.Principal{current}})
	got, err := r.refreshAttributes(attribs)
	if err != nil {
		t.Fatalf("refresh failed: %v", err)
	}
	if got == nil {
		t.Fatal("refresh returned no attribute")
	}
	items := got.GroupPrincipals["githubapp"].Items
	if len(items) != 1 || items[0].Name != current.Name {
		t.Fatalf("current membership was not stored: %+v", items)
	}
}
