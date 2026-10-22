package cwfunctional

import (
	"encoding/json"
	"net/http"
	"strings"
	"testing"

	"github.com/QuantumNous/new-api/model"
)

type userItem struct {
	Id       int    `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Role     int    `json:"role"`
	Status   int    `json:"status"`
	Group    string `json:"group"`
	Quota    int    `json:"quota"`
}

type userPage struct {
	Items []userItem `json:"items"`
	Total int        `json:"total"`
}

func pageFrom(t *testing.T, resp apiResponse) userPage {
	t.Helper()
	var page userPage
	if err := json.Unmarshal(resp.Data, &page); err != nil {
		t.Fatalf("decode user page: %v", err)
	}
	return page
}

func findUser(t *testing.T, page userPage, id int) userItem {
	t.Helper()
	for _, item := range page.Items {
		if item.Id == id {
			return item
		}
	}
	t.Fatalf("expected user %d in the response", id)
	return userItem{}
}

func TestAdminCanResetLowerRolePasskey(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedPasskey(t, aliceID)

	code, body := delete(t, engine, "/api/user/3/reset_passkey", adminToken, adminID)
	requireServed(t, code, body)
	if passkeyCount(t, aliceID) != 0 {
		t.Fatalf("a lower-role user's passkey was not reset")
	}
}

func TestRootCanResetAdminPasskey(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedPasskey(t, adminID)

	code, body := delete(t, engine, "/api/user/2/reset_passkey", rootToken, rootID)
	requireServed(t, code, body)
	if passkeyCount(t, adminID) != 0 {
		t.Fatalf("root could not reset a lower-role administrator's passkey")
	}
}

func TestRootCanResetAnotherRootPasskey(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedRoot2(t)
	seedPasskey(t, root2ID)

	code, body := delete(t, engine, "/api/user/5/reset_passkey", rootToken, rootID)
	requireServed(t, code, body)
	if passkeyCount(t, root2ID) != 0 {
		t.Fatalf("root could not reset another root account's passkey")
	}
}

func TestAdminCannotDisableHigherRoleTwoFA(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedTwoFA(t, rootID)

	code, body := delete(t, engine, "/api/user/1/2fa", adminToken, adminID)
	requireRefusal(t, code, body, "two-factor disable of a higher-role account")
	if twoFACount(t, rootID) != 1 {
		t.Fatalf("refused two-factor disable still removed the record")
	}
}

func TestRootCanDisableAdminTwoFA(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedTwoFA(t, adminID)

	code, body := delete(t, engine, "/api/user/2/2fa", rootToken, rootID)
	requireServed(t, code, body)
	if twoFACount(t, adminID) != 0 {
		t.Fatalf("root could not disable a lower-role administrator's two-factor record")
	}
}

func TestOwnProfileKeepsOwnNotificationSecrets(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/self", aliceToken, aliceID)
	requireServed(t, code, body)
	for _, marker := range []string{aliceWebhook, aliceGotify, aliceBark} {
		if !contains(body, marker) {
			t.Fatalf("the account's own profile no longer shows its notification credentials")
		}
	}
}

func TestGenerateTokenStillReturnsTokenToOwnerAndWorks(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/token", aliceToken, aliceID)
	resp := requireServed(t, code, body)
	var token string
	if err := json.Unmarshal(resp.Data, &token); err != nil {
		t.Fatalf("decode generated token: %v", err)
	}
	if len(token) < 20 {
		t.Fatalf("generated token was not returned to its owner")
	}

	code, body = get(t, engine, "/api/user/self", token, aliceID)
	requireServed(t, code, body)
}

func TestAccessTokenAuthenticationStillWorks(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/self", adminToken, adminID)
	resp := requireServed(t, code, body)
	var profile struct {
		Username string `json:"username"`
	}
	if err := json.Unmarshal(resp.Data, &profile); err != nil {
		t.Fatalf("decode profile: %v", err)
	}
	if profile.Username != "admin" {
		t.Fatalf("access-token authentication returned the wrong account")
	}
}

func TestAdminListKeepsNonSecretUserFields(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/", adminToken, adminID)
	page := pageFrom(t, requireServed(t, code, body))
	root := findUser(t, page, rootID)
	if root.Username != "root" || root.Role != 100 || root.Email != "root@example.test" || root.Group != "default" || root.Quota != 1000 {
		t.Fatalf("administrator user listing lost non-secret profile fields")
	}
	alice := findUser(t, page, aliceID)
	if alice.Username != "alice" || alice.Role != 1 || alice.Email != "alice@example.test" {
		t.Fatalf("administrator user listing lost a lower-role user's fields")
	}
}

func TestAdminSearchKeepsNonSecretUserFields(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/search?keyword=alice", adminToken, adminID)
	page := pageFrom(t, requireServed(t, code, body))
	alice := findUser(t, page, aliceID)
	if alice.Username != "alice" || alice.Email != "alice@example.test" || alice.Group != "default" {
		t.Fatalf("administrator user search lost non-secret profile fields")
	}
}

func TestAdminCanExportUsers(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/export", adminToken, adminID)
	requireServed(t, code, body)
	for _, email := range []string{"root@example.test", "admin@example.test", "alice@example.test", "admin2@example.test"} {
		if !contains(body, email) {
			t.Fatalf("administrator export no longer lists every account")
		}
	}
}

func TestCallerCanViewOwnManagementToken(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/2/token", adminToken, adminID)
	requireServed(t, code, body)
	if !contains(body, adminToken) {
		t.Fatalf("an account could not view its own management token")
	}
}

func TestAdminCanForceLogoutLowerRoleUser(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := post(t, engine, "/api/user/3/force_logout", adminToken, adminID, nil)
	requireServed(t, code, body)
	if storedToken(t, aliceID) != "" {
		t.Fatalf("the lower-role user's management token was not revoked")
	}
	code, body = get(t, engine, "/api/user/self", aliceToken, aliceID)
	requireRefusal(t, code, body, "authentication with a revoked token")
}

func TestAdminCanUpdateUserRecord(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	update := map[string]any{
		"id":       aliceID,
		"username": "alice",
		"group":    "vip",
		"remark":   "kept",
	}
	code, body := request(t, engine, http.MethodPut, "/api/user/", adminToken, adminID, update)
	requireServed(t, code, body)

	var stored model.User
	if err := model.DB.First(&stored, aliceID).Error; err != nil {
		t.Fatalf("load updated user: %v", err)
	}
	if stored.Group != "vip" || stored.Remark != "kept" {
		t.Fatalf("administrator user update no longer persists")
	}
}

func contains(body []byte, marker string) bool {
	return marker != "" && strings.Contains(string(body), marker)
}

func TestAdminSupportTokenListKeepsTokenMetadata(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedTokens(t)

	code, body := get(t, engine, "/api/user/3/tokens", adminToken, adminID)
	resp := requireServed(t, code, body)
	var listing struct {
		Items []struct {
			Id     int    `json:"id"`
			UserId int    `json:"user_id"`
			Name   string `json:"name"`
		} `json:"items"`
	}
	if err := json.Unmarshal(resp.Data, &listing); err != nil {
		t.Fatalf("decode API key listing: %v", err)
	}
	if len(listing.Items) != 1 || listing.Items[0].UserId != aliceID || listing.Items[0].Name != "alice-api-key" {
		t.Fatalf("administrator support view lost non-secret API key metadata")
	}
}

func TestAdminCachedProfileKeepsNonSecretFields(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)

	code, body := get(t, engine, "/api/user/3/profile", adminToken, adminID)
	resp := requireServed(t, code, body)
	var profile struct {
		Username string `json:"username"`
		Email    string `json:"email"`
		Group    string `json:"group"`
		Quota    int    `json:"quota"`
		Status   int    `json:"status"`
	}
	if err := json.Unmarshal(resp.Data, &profile); err != nil {
		t.Fatalf("decode cached account profile: %v", err)
	}
	if profile.Username != "alice" || profile.Email != "alice@example.test" || profile.Group != "default" || profile.Quota != 1000 || profile.Status != 1 {
		t.Fatalf("cached account profile lost non-secret fields")
	}
}

func TestAdminCanBindSignInIdentityToLowerRoleUser(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedOAuthProvider(t)

	code, body := post(t, engine, "/api/user/3/oauth/bindings", adminToken, adminID, oauthBindingRequest{ProviderId: oauthProviderID, ProviderUserId: "cwb-support-alice"})
	requireServed(t, code, body)
	if oauthBindingCount(t, aliceID) != 1 {
		t.Fatalf("an outranking administrator could not add a lower-role account's sign-in identity")
	}
}

func TestRootCanBindSignInIdentityToAnotherRoot(t *testing.T) {
	engine := newTestServer(t)
	seedUsers(t)
	seedRoot2(t)
	seedOAuthProvider(t)

	code, body := post(t, engine, "/api/user/5/oauth/bindings", rootToken, rootID, oauthBindingRequest{ProviderId: oauthProviderID, ProviderUserId: "cwb-support-root2"})
	requireServed(t, code, body)
	if oauthBindingCount(t, root2ID) != 1 {
		t.Fatalf("root could not add another root account's sign-in identity")
	}
}
