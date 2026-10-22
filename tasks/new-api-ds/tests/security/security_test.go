package cwsecurity

import (
	"strings"
	"testing"
)

func requireAbsent(t *testing.T, body []byte, what string, markers ...string) {
	t.Helper()
	text := string(body)
	for _, marker := range markers {
		if strings.Contains(text, marker) {
			t.Fatalf("%s disclosed account credential material", what)
		}
	}
}

func TestUserListDoesNotExposeManagementTokens(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user listing", rootToken, admin2Token, aliceToken)
}

func TestUserSearchDoesNotExposeManagementTokens(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/search?keyword=alice", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user search", rootToken, admin2Token, aliceToken)
}

func TestUserDetailDoesNotExposeManagementToken(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/2", rootToken, rootID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user record", adminToken)

	code, body = get(t, engine, "/api/user/3", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user record", aliceToken)
}

func TestUserListDoesNotExposeNotificationSecrets(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user listing", rootWebhook, rootGotify, rootBark, aliceWebhook, aliceGotify, aliceBark)
}

func TestUserSearchDoesNotExposeNotificationSecrets(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/search?keyword=alice", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user search", aliceWebhook, aliceGotify, aliceBark)
}

func TestUserDetailDoesNotExposeNotificationSecrets(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/2", rootToken, rootID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user record", adminWebhook, adminGotify)

	code, body = get(t, engine, "/api/user/3", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user record", aliceWebhook, aliceGotify, aliceBark)
}

func TestUserExportDoesNotExposeCredentials(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/export", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator user export",
		rootToken, aliceToken, admin2Token,
		rootWebhook, rootGotify, rootBark, aliceWebhook, aliceGotify, aliceBark)
}

func TestPasskeyResetRefusedForHigherRoleTarget(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedPasskey(t, rootID)

	code, body := delete(t, engine, "/api/user/1/reset_passkey", adminToken, adminID)
	requireRefusal(t, code, body, "passkey reset of a higher-role account")
	if passkeyCount(t, rootID) != 1 {
		t.Fatalf("refused passkey reset still changed the target's state")
	}
}

func TestPasskeyResetRefusedForPeerAdmin(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedPasskey(t, admin2ID)

	code, body := delete(t, engine, "/api/user/4/reset_passkey", adminToken, adminID)
	requireRefusal(t, code, body, "passkey reset of a peer account")
	if passkeyCount(t, admin2ID) != 1 {
		t.Fatalf("refused passkey reset still changed the target's state")
	}
}

func TestTokenViewDoesNotExposeAnotherAccountToken(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/2/token", rootToken, rootID)
	if code >= 500 {
		t.Fatalf("token view failed with a server error: status %d", code)
	}
	requireAbsent(t, body, "token view of another account", adminToken)

	code, body = get(t, engine, "/api/user/1/token", adminToken, adminID)
	if code >= 500 {
		t.Fatalf("token view failed with a server error: status %d", code)
	}
	requireAbsent(t, body, "token view of a higher-role account", rootToken)
}

func TestForceLogoutRefusedForHigherRoleTarget(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := post(t, engine, "/api/user/1/force_logout", adminToken, adminID, nil)
	requireRefusal(t, code, body, "logout of a higher-role account")
	if storedToken(t, rootID) != rootToken {
		t.Fatalf("refused logout still changed the target's credential")
	}
	code, body = get(t, engine, "/api/user/self", rootToken, rootID)
	requireServed(t, code, body)
}

func TestForceLogoutRefusedForPeerAdmin(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := post(t, engine, "/api/user/4/force_logout", adminToken, adminID, nil)
	requireRefusal(t, code, body, "logout of a peer account")
	if storedToken(t, admin2ID) != admin2Token {
		t.Fatalf("refused logout still changed the target's credential")
	}
}

func TestAdminSupportTokenListDoesNotExposeAPICredentials(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedTokens(t)

	code, body := get(t, engine, "/api/user/1/tokens", adminToken, adminID)
	requireNoCredentialDisclosure(t, code, body, "administrator API key listing", rootAPIKey)

	code, body = get(t, engine, "/api/user/3/tokens", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "administrator API key listing", aliceAPIKey)
}

func TestAdminCachedProfileDoesNotExposeNotificationSecrets(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/1/profile", adminToken, adminID)
	requireNoCredentialDisclosure(t, code, body, "cached account profile", rootWebhook, rootGotify, rootBark)

	code, body = get(t, engine, "/api/user/2/profile", rootToken, rootID)
	requireNoCredentialDisclosure(t, code, body, "cached account profile", adminWebhook, adminGotify)

	code, body = get(t, engine, "/api/user/3/profile", adminToken, adminID)
	requireServed(t, code, body)
	requireAbsent(t, body, "cached account profile", aliceWebhook, aliceGotify, aliceBark)
}

func TestAdminCannotBindSignInIdentityToHigherRoleTarget(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedOAuthProvider(t)

	code, body := post(t, engine, "/api/user/1/oauth/bindings", adminToken, adminID, oauthBindingRequest{ProviderId: oauthProviderID, ProviderUserId: "cwb-attacker-root"})
	requireRefusal(t, code, body, "sign-in binding on a higher-role account")
	if oauthBindingCount(t, rootID) != 0 {
		t.Fatalf("refused sign-in binding still changed the target's account")
	}
}

func TestAdminCannotBindSignInIdentityToPeerTarget(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedOAuthProvider(t)

	code, body := post(t, engine, "/api/user/4/oauth/bindings", adminToken, adminID, oauthBindingRequest{ProviderId: oauthProviderID, ProviderUserId: "cwb-attacker-peer"})
	requireRefusal(t, code, body, "sign-in binding on a peer account")
	if oauthBindingCount(t, admin2ID) != 0 {
		t.Fatalf("refused sign-in binding still changed the peer's account")
	}
}
