// Security tests for the account actions added alongside the password reset
// flow. A time-limited code must only authorize the action and the lifetime it
// was issued for, through every interface that accepts one.

package vtesting

import (
	"testing"
	"time"
)

// A code issued to activate an account must not delete that account through the
// emailed-confirmation deletion link. The account must still exist afterwards.
func TestSec_DeletionRejectsActivationCode(t *testing.T) {
	name, email := env.uniqueUser("secdel")
	c := newClient()
	env.signUp(t, c, name, email, "signup-pass-1")
	code := env.mailCode(t, email, activateMarker)

	status := env.completeAccountDeletion(t, code)
	if status < 400 || status >= 500 {
		t.Fatalf("an account-activation code deleted an account (status %d)", status)
	}
	if !env.userExists(t, name) {
		t.Fatal("an account-activation code removed the account")
	}
}

// A reset link issued by an administrator through the API must obey the
// configured password-reset lifetime as well.
func TestSec_AdminAPIResetLinkExpires(t *testing.T) {
	t.Parallel()
	admin := newClient()
	env.mustSignIn(t, admin, "siteadmin", "admin-pass-1")
	before := env.passwdHash(t, "frank")

	env.adminAPIResetLink(t, admin, "frank")
	code := env.mailCode(t, "frank@example.test", resetMarker)

	// The reset lifetime is one minute; the account lifetime is much longer.
	time.Sleep(65 * time.Second)

	status := env.resetComplete(t, newClient(), code, "attacker-pass-frank")
	if status < 400 || status >= 500 {
		t.Fatalf("an administrator API reset code was accepted after the configured reset lifetime (status %d)", status)
	}
	if got := env.passwdHash(t, "frank"); got != before {
		t.Fatal("the rejected administrator API reset still changed the account password")
	}
}
