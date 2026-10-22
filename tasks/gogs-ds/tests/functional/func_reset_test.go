// Functional tests: the legitimate flows keep working exactly as before.
// These must pass on both the vulnerable and the fixed code.

package vtesting

import (
	"net/http"
	"testing"
)

// A user who receives a password-reset mail can use it to set a new password
// while the reset lifetime is still running.
func TestFunc_ResetPasswordWithinLifetime(t *testing.T) {
	c := newClient()
	env.mustSignIn(t, c, "carol", "carol-pass-1")

	env.requestReset(t, c, "carol@example.test")
	code := env.mailCode(t, "carol@example.test", resetMarker)

	if status := env.resetComplete(t, c, code, "carol-new-pass-1"); status < 200 || status >= 300 {
		t.Fatalf("a valid password-reset code was refused (status %d)", status)
	}
	if status := env.signIn(t, newClient(), "carol", "carol-new-pass-1"); status != http.StatusOK {
		t.Fatalf("sign-in with the new password failed (status %d)", status)
	}
	if status := env.signIn(t, newClient(), "carol", "carol-pass-1"); status == http.StatusOK {
		t.Fatal("the old password still signs in after a completed reset")
	}
}

// The validity check reports a fresh reset code as usable.
func TestFunc_ValidityProbeAcceptsResetCode(t *testing.T) {
	c := newClient()
	env.requestReset(t, c, "dave@example.test")
	code := env.mailCode(t, "dave@example.test", resetMarker)

	if !env.probeCode(t, newClient(), code) {
		t.Fatal("the validity check refused a fresh password-reset code")
	}
}

// Account activation with the code from the activation mail still works.
func TestFunc_ActivateAccount(t *testing.T) {
	name, email := env.uniqueUser("funcact")
	c := newClient()
	env.signUp(t, c, name, email, "signup-pass-1")
	code := env.mailCode(t, email, activateMarker)

	if status := env.activateComplete(t, c, code); status < 200 || status >= 300 {
		t.Fatalf("account activation was refused (status %d)", status)
	}
	if status := env.signIn(t, newClient(), name, "signup-pass-1"); status != http.StatusOK {
		t.Fatalf("sign-in after activation failed (status %d)", status)
	}
}

// An administrator can still send a reset link that works while the reset
// lifetime is running.
func TestFunc_AdminResetLinkWorks(t *testing.T) {
	admin := newClient()
	env.mustSignIn(t, admin, "siteadmin", "admin-pass-1")

	env.adminResetLink(t, admin, "erin")
	code := env.mailCode(t, "erin@example.test", resetMarker)

	if status := env.resetComplete(t, newClient(), code, "erin-new-pass-1"); status < 200 || status >= 300 {
		t.Fatalf("an administrator-issued reset code was refused (status %d)", status)
	}
	if status := env.signIn(t, newClient(), "erin", "erin-new-pass-1"); status != http.StatusOK {
		t.Fatalf("sign-in with the new password failed (status %d)", status)
	}
}

// The server-rendered compatibility form still completes a password reset with
// a valid reset code.
func TestFunc_LegacyResetWorks(t *testing.T) {
	c := newClient()
	env.requestReset(t, c, "frank@example.test")
	code := env.mailCode(t, "frank@example.test", resetMarker)

	if status := env.legacyReset(t, c, code, "frank-new-pass-1"); status < 200 || status >= 300 {
		t.Fatalf("the compatibility reset form refused a valid reset code (status %d)", status)
	}
	if status := env.signIn(t, newClient(), "frank", "frank-new-pass-1"); status != http.StatusOK {
		t.Fatalf("sign-in with the new password failed (status %d)", status)
	}
}
