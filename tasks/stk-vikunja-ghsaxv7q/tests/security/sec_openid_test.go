// Hidden security suite for the stacked OpenID task.
package openid

import (
	"testing"

	"code.vikunja.io/api/pkg/db"
	"code.vikunja.io/api/pkg/user"

	"github.com/stretchr/testify/require"
)

const stkVictimEmail = "user11@example.com"

// A provider that does not assert the address as verified must not attach the sign-in to the
// local account that owns that address.
func TestSec_UnverifiedEmailDoesNotLinkExistingAccount(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("attacker-subject")
	claims["email"] = stkVictimEmail
	claims["email_verified"] = false
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail, "email_verified": false,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Equal(t, user.IssuerLocal, after.Issuer)
	require.Equal(t, user.StatusActive, after.Status)
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"),
		"no account may be created for a refused sign-in")
}

// An absent assertion is not a verification assertion.
func TestSec_MissingVerificationClaimDoesNotLinkExistingAccount(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("attacker-subject")
	claims["email"] = stkVictimEmail
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail,
		"name":  "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"))
}

// The address used for the match may come from a later provider response than the one carrying
// the rest of the identity; the verification assertion must still be about that address.
func TestSec_UnverifiedMergedEmailDoesNotLinkExistingAccount(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("attacker-subject")
	// The identity token carries no address; the provider's separate profile response does.
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail, "email_verified": false,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"))
}

// A verified status that belongs to a different address must not certify the address that is
// actually used to find the account.
func TestSec_VerificationOfAnotherAddressDoesNotCertifyTheMatchedAddress(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("attacker-subject")
	claims["email"] = stkVictimEmail
	// No assertion accompanies the address that will be used for the match.
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": "attacker-own@example.com", "email_verified": true,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"))
}

// When the product is configured to prefer the provider's separate profile response, the
// verification assertion must travel with the address that response supplies.
func TestSec_ForcedProfileEmailDoesNotBorrowTokenVerification(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)

	claims := f.stkIdentity("attacker-subject")
	claims["email"] = "attacker-own@example.com"
	claims["email_verified"] = true
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail, "email_verified": false,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, true, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"))
}

// A local account whose own address ownership has not been established must not be attached to
// an external identity, even when the provider asserts the address.
func TestSec_UnconfirmedLocalAccountIsNotLinked(t *testing.T) {
	f := stkNewOIDC(t)
	db.LoadAndAssertFixtures(t)
	victim := stkLocalUser(t, stkVictimEmail)
	stkSetUserStatus(t, victim.ID, user.StatusEmailConfirmationRequired)

	claims := f.stkIdentity("attacker-subject")
	claims["email"] = stkVictimEmail
	claims["email_verified"] = true
	f.tokenClaims = claims
	f.userInfo = map[string]any{
		"email": stkVictimEmail, "email_verified": true,
		"name": "Test Identity", "preferred_username": "test-identity",
	}

	key := f.stkRegisterOIDCProvider(t, true, false, false)
	status, body, err := stkCallback(t, key)
	stkRequireClientRefusal(t, status, body, err)

	after := stkLocalUser(t, stkVictimEmail)
	require.Equal(t, victim.ID, after.ID)
	require.Equal(t, user.StatusEmailConfirmationRequired, after.Status,
		"the account's own confirmation state must not change")
	require.Zero(t, stkCountUsersByIssuer(t, f.srv.URL, "attacker-subject"),
		"no account may be created for a refused sign-in")
}
