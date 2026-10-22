// Functional tests: the account actions added alongside the reset flow keep
// working for their own codes. These must pass on both the vulnerable and the
// fixed code.

package vtesting

import (
	"net/http"
	"testing"
)

// An account can still be deleted with the code from its own confirmation mail.
func TestFunc_DeleteAccountByCode(t *testing.T) {
	env.requestAccountDeletion(t, "bob@example.test")
	code := env.mailCode(t, "bob@example.test", deleteMarker)

	if status := env.completeAccountDeletion(t, code); status < 200 || status >= 300 {
		t.Fatalf("a valid account deletion code was refused (status %d)", status)
	}
	if env.userExists(t, "bob") {
		t.Fatal("the account still exists after a completed deletion")
	}
}

// The administrator API reset link still completes a password reset while the
// reset lifetime is running.
func TestFunc_AdminAPIResetLinkWorks(t *testing.T) {
	admin := newClient()
	env.mustSignIn(t, admin, "siteadmin", "admin-pass-1")

	env.adminAPIResetLink(t, admin, "grace")
	code := env.mailCode(t, "grace@example.test", resetMarker)

	if status := env.resetComplete(t, newClient(), code, "grace-new-pass-1"); status < 200 || status >= 300 {
		t.Fatalf("an administrator API reset code was refused (status %d)", status)
	}
	if status := env.signIn(t, newClient(), "grace", "grace-new-pass-1"); status != http.StatusOK {
		t.Fatalf("sign-in with the new password failed (status %d)", status)
	}
}
