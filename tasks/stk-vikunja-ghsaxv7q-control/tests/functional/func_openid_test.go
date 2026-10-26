// Hidden functional suite for the stacked OpenID task: legitimate sign-ins keep working.
package openid

import (
	"testing"

	"code.vikunja.io/api/pkg/db"
	"code.vikunja.io/api/pkg/user"

	"github.com/stretchr/testify/require"
)

// A first-time sign-in with an address that belongs to no local account creates an account even
// when the provider does not assert the address as verified.
func TestFunc_UnverifiedEmailCreatesNewAccount(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)

	claims := f.stkIdentity("new-subject")
	claims["email"] = "stk-brand-new@example.com"
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": "stk-brand-new@example.com",
		"name":  "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	require.NoError(t, err)
	require.Equal(t, 200, status)

	id := stkTokenUserID(t, body)
	require.NotZero(t, id)
	created := stkCountUsersByIssuer(t, f.srv.URL, "new-subject")
	require.EqualValues(t, 1, created)
}

// An account already bound to the provider keeps signing in regardless of the address's
// verification status.
func TestFunc_AlreadyLinkedAccountKeepsWorking(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)

	linked := stkInsertLinkedUser(t, f.srv.URL, "linked-subject", "stk-linked@example.com")

	claims := f.stkIdentity("linked-subject")
	claims["email"] = "stk-linked@example.com"
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": "stk-linked@example.com",
		"name":  "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireSessionFor(t, linked.ID, status, body, err)
}

// Some providers send the verification flag as a string; that must not break the sign-in.
func TestFunc_StringVerificationClaimDoesNotBreakSignIn(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)

	claims := f.stkIdentity("string-subject")
	claims["email"] = "stk-string@example.com"
	claims["email_verified"] = "true"
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": "stk-string@example.com",
		"name":  "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	require.NoError(t, err)
	require.Equal(t, 200, status)

	id := stkTokenUserID(t, body)
	require.NotZero(t, id)
	require.EqualValues(t, 1, stkCountUsersByIssuer(t, f.srv.URL, "string-subject"))
}

// A verified address that belongs to an active local account still links, as it did before.
func TestFunc_VerifiedEmailLinksActiveLocalAccount(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("verified-subject")
	claims["email"] = stkVictimEmail
	claims["email_verified"] = true
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail, "email_verified": true,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireSessionFor(t, victim.ID, status, body, err)
}

// Username-based matching is a separate, explicitly configured behaviour and keeps working.
func TestFunc_UsernameFallbackKeepsWorking(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("user11")
	claims["email"] = "stk-username-only@example.com"
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": "stk-username-only@example.com",
		"name":  "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, false, false, true)
	status, body, err := stkCallback(t, key)
	stkRequireSessionFor(t, victim.ID, status, body, err)
	if victim.Status != user.StatusActive {
		t.Fatalf("fixture account must be active")
	}
}
