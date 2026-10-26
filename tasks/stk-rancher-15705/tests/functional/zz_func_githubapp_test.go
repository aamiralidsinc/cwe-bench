package githubapp

import "testing"

// A legitimate member keeps every team the installation data records for them.
func TestFunc_LegitimateMemberKeepsOwnTeams(t *testing.T) {
	data := zzSecFixture(t)
	got := data.listTeamsForUser("test-user")

	seen := map[string]int{}
	for _, a := range got {
		seen[a.Login] = a.ID
	}
	if id, ok := seen["dev-team"]; !ok || id != 34567 {
		t.Fatalf("legitimate team example/dev-team is missing or wrong: %v", got)
	}
	if id, ok := seen["dev-team2"]; !ok || id != 23468 {
		t.Fatalf("legitimate team other-org/dev-team2 is missing or wrong: %v", got)
	}
}

// Team discovery for granting access must remain membership-blind: an administrator
// can find and grant any team of an installed organization.
func TestFunc_TeamSearchRemainsMembershipBlind(t *testing.T) {
	data := zzSecFixture(t)
	got := data.searchTeams("admin")

	seen := map[string]bool{}
	for _, a := range got {
		seen[a.Login] = true
	}
	for _, want := range []string{"admin-team", "admin-team2"} {
		if !seen[want] {
			t.Fatalf("team %q is no longer discoverable for granting: %+v", want, got)
		}
	}
}

// The full team list of every installed organization stays available.
func TestFunc_AllTeamsStayListed(t *testing.T) {
	data := zzSecFixture(t)
	got := data.listTeams()

	seen := map[string]bool{}
	for _, a := range got {
		seen[a.Login] = true
	}
	for _, want := range []string{"dev-team", "admin-team", "dev-team2", "admin-team2"} {
		if !seen[want] {
			t.Fatalf("team %q is missing from the organization team list", want)
		}
	}
}

// A user's organization principals are unchanged.
func TestFunc_OrgPrincipalsUnchanged(t *testing.T) {
	data := zzSecFixture(t)
	got := data.listOrgsForUser("test-user")

	seen := map[string]bool{}
	for _, a := range got {
		seen[a.Login] = true
	}
	for _, want := range []string{"example", "other-org"} {
		if !seen[want] {
			t.Fatalf("organization %q is missing from the user's organization principals", want)
		}
	}
}
