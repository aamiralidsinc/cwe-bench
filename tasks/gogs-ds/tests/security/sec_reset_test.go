// Security tests: a time-limited code must only authorize the purpose and the
// lifetime it was issued for. Each test drives the real HTTP entry point and
// asserts a client error with no side effect (the stored password hash is
// unchanged). They fail on the vulnerable code and pass on a correct fix.

package vtesting

import (
	"testing"
	"time"
)

// After the configured password-reset lifetime has passed, the code from a
// password-reset mail must not set a new password.
func TestSec_ResetCodeExpires(t *testing.T) {
	t.Parallel()
	c := newClient()
	before := env.passwdHash(t, "alice")

	env.requestReset(t, c, "alice@example.test")
	code := env.mailCode(t, "alice@example.test", resetMarker)

	// The reset lifetime is one minute; the account-activation lifetime is much
	// longer. Wait until the reset lifetime has certainly passed.
	time.Sleep(65 * time.Second)

	status := env.resetComplete(t, newClient(), code, "attacker-pass-alice")
	if status < 400 || status >= 500 {
		t.Fatalf("a password-reset code was accepted after the configured reset lifetime (status %d)", status)
	}
	if got := env.passwdHash(t, "alice"); got != before {
		t.Fatal("the rejected reset request still changed the account password")
	}
}

// A code issued to activate an account must not set a password through the
// password-reset completion route.
func TestSec_ActivationCodeCannotResetPassword(t *testing.T) {
	name, email := env.uniqueUser("secact")
	c := newClient()
	env.signUp(t, c, name, email, "signup-pass-1")
	code := env.mailCode(t, email, activateMarker)
	before := env.passwdHash(t, name)

	status := env.resetComplete(t, newClient(), code, "attacker-pass-act")
	if status < 400 || status >= 500 {
		t.Fatalf("an account-activation code set a password (status %d)", status)
	}
	if got := env.passwdHash(t, name); got != before {
		t.Fatal("an account-activation code changed the account password")
	}
}

// The password-reset validity check must not report a code issued for account
// activation as usable for a password reset.
func TestSec_ValidityProbeRejectsActivationCode(t *testing.T) {
	name, email := env.uniqueUser("secprobe")
	c := newClient()
	env.signUp(t, c, name, email, "signup-pass-1")
	code := env.mailCode(t, email, activateMarker)

	if env.probeCode(t, newClient(), code) {
		t.Fatal("the password-reset validity check reported an account-activation code as valid")
	}
}

// A reset link issued by an administrator must obey the password-reset
// lifetime as well; it is not a way to hand out long-lived reset codes.
func TestSec_AdminResetLinkExpires(t *testing.T) {
	t.Parallel()
	admin := newClient()
	env.mustSignIn(t, admin, "siteadmin", "admin-pass-1")
	before := env.passwdHash(t, "bob")

	env.adminResetLink(t, admin, "bob")
	code := env.mailCode(t, "bob@example.test", resetMarker)

	time.Sleep(65 * time.Second)

	status := env.resetComplete(t, newClient(), code, "attacker-pass-bob")
	if status < 400 || status >= 500 {
		t.Fatalf("an administrator-issued reset code was accepted after the configured reset lifetime (status %d)", status)
	}
	if got := env.passwdHash(t, "bob"); got != before {
		t.Fatal("the rejected administrator-issued reset still changed the account password")
	}
}

// A code issued for one purpose must not complete a different account action.
// A password-reset code submitted as account confirmation must be refused and
// must leave the account untouched.
func TestSec_ResetCodeCannotActivateAccount(t *testing.T) {
	// The suite configures a one-minute reset lifetime and codes are minted at
	// minute granularity. Even a wrong-purpose code must still be unexpired for
	// the refusal to prove anything, so do not mint in the last seconds of a
	// minute.
	if s := time.Now().Second(); s >= 50 {
		time.Sleep(time.Duration(60-s) * time.Second)
	}
	env.requestReset(t, newClient(), "grace@example.test")
	code := env.mailCode(t, "grace@example.test", resetMarker)
	before := env.rands(t, "grace")

	status := env.activateComplete(t, newClient(), code)
	if status < 400 || status >= 500 {
		t.Fatalf("a password-reset code completed account confirmation (status %d)", status)
	}
	if got := env.rands(t, "grace"); got != before {
		t.Fatal("the refused confirmation still modified the account")
	}
}

// The server-rendered compatibility reset form must enforce the same purpose
// rule as the web API: an activation code must not set a password there.
func TestSec_LegacyResetRejectsActivationCode(t *testing.T) {
	name, email := env.uniqueUser("seclegacy")
	c := newClient()
	env.signUp(t, c, name, email, "signup-pass-1")
	code := env.mailCode(t, email, activateMarker)
	before := env.passwdHash(t, name)

	status := env.legacyReset(t, newClient(), code, "attacker-pass-legacy")
	if status < 400 || status >= 500 {
		t.Fatalf("the compatibility reset form accepted an account-activation code (status %d)", status)
	}
	if got := env.passwdHash(t, name); got != before {
		t.Fatal("the compatibility reset form changed the account password using an activation code")
	}
}
