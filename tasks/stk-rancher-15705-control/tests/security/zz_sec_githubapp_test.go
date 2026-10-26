package githubapp

import "testing"

func zzSecFixture(t *testing.T) *gitHubAppData {
	t.Helper()
	data := newGitHubAppData()
	data.addOrg(1234567, "example", "Example Org", "https://example.com/avatar1.jpg")
	data.addTeamToOrg("example", 34567, "dev-team", "dev team", "https://example.com/avatar.jpg", "https://example.com/org/example/team/dev-team")
	data.addTeamToOrg("example", 45678, "admin-team", "admin team", "https://example.com/avatar.jpg", "https://example.com/org/example/team/admin-team")
	data.addMemberToTeamInOrg("example", "dev-team", 1001, "test-user", "Test User", "https://example.com/avatar2.jpg", "https://example.com/html")
	// A membership entry naming a team the installation data does not contain.
	data.addMemberToTeamInOrg("example", "example", 1001, "test-user", "Test User", "https://example.com/avatar2.jpg", "https://example.com/html")

	data.addOrg(2345678, "other-org", "Other Org", "https://example.com/avatar2.jpg")
	data.addTeamToOrg("other-org", 23468, "dev-team2", "dev team 2", "https://example.com/avatar.jpg", "https://example.com/org/other-org/team/dev-team2")
	data.addTeamToOrg("other-org", 34579, "admin-team2", "admin team 2", "https://example.com/avatar.jpg", "https://example.com/org/other-org/team-dev-team2")
	data.addMemberToTeamInOrg("other-org", "dev-team2", 1001, "test-user", "Test User", "https://example.com/avatar2.jpg", "https://example.com/html")
	data.addMemberToTeamInOrg("other-org", "admin-team2", 1002, "test-user2", "Other User", "https://example.com/avatar3.jpg", "https://example.com/htmlpage")
	return data
}

// A user who belongs to one team in an organization must not become a member of the
// organization's other teams.
func TestSec_TeamsForUserExcludesNonMemberTeams(t *testing.T) {
	data := zzSecFixture(t)
	got := data.listTeamsForUser("test-user")

	seen := map[string]bool{}
	for _, a := range got {
		seen[a.Login] = true
		if a.Login == "admin-team" {
			t.Fatalf("test-user is not a member of example/admin-team, but it was returned")
		}
		if a.Login == "admin-team2" {
			t.Fatalf("test-user is not a member of other-org/admin-team2, but it was returned")
		}
	}
	for _, want := range []string{"dev-team", "dev-team2"} {
		if !seen[want] {
			t.Fatalf("legitimate team %q is missing from the user's membership", want)
		}
	}
}

// The same team slug in two organizations is two different teams. A membership must
// resolve against the organization that recorded it.
func TestSec_TeamsForUserResolvesMembershipPerOrg(t *testing.T) {
	data := newGitHubAppData()
	data.addOrg(101, "org-a", "Org A", "https://example.com/a.jpg")
	data.addTeamToOrg("org-a", 5001, "shared-team", "shared team", "https://example.com/a.jpg", "https://example.com/org-a/team/shared-team")
	data.addTeamToOrg("org-a", 5003, "a-only", "a only", "https://example.com/a.jpg", "https://example.com/org-a/team/a-only")
	data.addOrg(202, "org-b", "Org B", "https://example.com/b.jpg")
	data.addTeamToOrg("org-b", 5002, "shared-team", "shared team", "https://example.com/b.jpg", "https://example.com/org-b/team/shared-team")
	data.addTeamToOrg("org-b", 5004, "b-only", "b only", "https://example.com/b.jpg", "https://example.com/org-b/team/b-only")
	data.addMemberToTeamInOrg("org-a", "shared-team", 1001, "alice", "Alice", "https://example.com/alice.jpg", "https://example.com/alice")
	data.addMemberToTeamInOrg("org-b", "b-only", 1001, "alice", "Alice", "https://example.com/alice.jpg", "https://example.com/alice")

	got := data.listTeamsForUser("alice")
	var shared []string
	var sharedIDs []int
	present := map[string]bool{}
	for _, a := range got {
		present[a.Login] = true
		if a.Login == "shared-team" {
			shared = append(shared, a.HTMLURL)
			sharedIDs = append(sharedIDs, a.ID)
		}
		if a.Login == "a-only" {
			t.Fatalf("alice is not a member of org-a/a-only, but it was returned")
		}
	}
	if len(shared) != 1 {
		t.Fatalf("expected exactly one shared-team membership, got %d (%v)", len(shared), shared)
	}
	if sharedIDs[0] != 5001 {
		t.Fatalf("shared-team resolved against the wrong organization: id %d", sharedIDs[0])
	}
	if !present["b-only"] {
		t.Fatalf("legitimate team org-b/b-only is missing from the user's membership")
	}
}

// A membership entry the installation data cannot resolve must be skipped, not turned
// into an account with no identity, and the current membership must be exact.
func TestSec_TeamsForUserSkipsUnknownSlugs(t *testing.T) {
	data := zzSecFixture(t)
	got := data.listTeamsForUser("test-user")

	if len(got) != 2 {
		t.Fatalf("expected exactly the two current memberships, got %d: %+v", len(got), got)
	}
	for _, a := range got {
		if a.ID == 0 || a.Login == "" {
			t.Fatalf("returned an unresolved team account: %+v", a)
		}
	}
}
