package requests

import (
	"testing"

	apiv3 "github.com/rancher/rancher/pkg/apis/management.cattle.io/v3"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// A legacy token whose group principal has no provider identity to consult keeps
// working exactly as before.
func TestFunc_LegacyTokenKeepsUnverifiableGroups(t *testing.T) {
	legacy := apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "legacyidp_group://777"},
		LoginName:     "legacy-group",
		Provider:      "legacyidp",
		PrincipalType: "group",
	}
	token := zzAuthToken("token-legacy", "", []apiv3.Principal{legacy})
	f := zzNewAuthFixture(t, token, zzAuthUser(), zzAuthAttribs(map[string]apiv3.Principals{}))
	resp := zzAuthenticate(t, f, token)

	for _, g := range resp.Groups {
		if g == legacy.Name {
			return
		}
	}
	t.Fatalf("a legacy token's group principal was dropped: %v", resp.Groups)
}

// Membership stored in the user's current attribute still grants access.
func TestFunc_StoredMembershipStillGrants(t *testing.T) {
	stale := apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_team://45678"},
		LoginName:     "admin-team",
		Provider:      "githubapp",
		PrincipalType: "group",
	}
	current := apiv3.Principal{
		ObjectMeta:    metav1.ObjectMeta{Name: "githubapp_team://34567"},
		LoginName:     "dev-team",
		Provider:      "githubapp",
		PrincipalType: "group",
	}
	token := zzAuthToken("token-current", "githubapp", []apiv3.Principal{stale})
	attribs := zzAuthAttribs(map[string]apiv3.Principals{
		"githubapp": {Items: []apiv3.Principal{current}},
	})
	f := zzNewAuthFixture(t, token, zzAuthUser(), attribs)
	resp := zzAuthenticate(t, f, token)

	hasCurrent := false
	for _, g := range resp.Groups {
		if g == current.Name {
			hasCurrent = true
		}
		if g == stale.Name {
			t.Fatalf("a stale token membership granted access next to the current one")
		}
	}
	if !hasCurrent {
		t.Fatalf("current membership was not granted: %v", resp.Groups)
	}
}
