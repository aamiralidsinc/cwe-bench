# Security review: admin-panel sign-in and multi-factor flows

We operate an admin panel built on the PHP/Laravel framework in `/app`. A review of
the panel's sign-in and multi-factor-authentication flows, together with some
external probing, surfaced a group of problems. Each one is reproducible against a
running panel through ordinary HTTP / Livewire interactions — the same requests the
browser makes when a person uses the login screen, the second-factor challenge, or
the account-security area. Please investigate the panel's authentication surface and
harden it. The legitimate behaviour described at the end must keep working. Wherever a
request has to be refused, answer it as a client error (for example forbidden, or a
validation error), not by failing with a server error.

## Observed problems

### Anonymous file staging on the sign-in screens
Before anyone has authenticated, the login screen still honours the framework's
temporary-file-upload requests. By replaying the browser's upload calls against the
login component and pointing them at an arbitrary target, an anonymous visitor can
push files into the application's temporary storage — even though the login screen
exposes no file-upload field whatsoever. This lets an unauthenticated user consume
disk and storage at will. Temporary uploads should only ever be accepted for a form
field that genuinely accepts a file.

### Password-validity oracle for accounts denied entry to a panel
When an account has multi-factor authentication enabled but is not allowed into the
panel it is signing in to, submitting its *correct* password makes the login advance
to the second-factor challenge, whereas a *wrong* password returns the generic
"these credentials do not match" error. An unauthenticated attacker can therefore
learn whether a given password is valid for such an account simply by observing which
response comes back (and with an email-based second factor this even sends a login
code to the victim). A denied account must return the same generic failure whether or
not the password was correct, and must never advance to the challenge.

### Authenticator codes stay usable after a newer code is accepted
The authenticator-app (TOTP) step only treats the exact same code as already spent.
After a user signs in with the current code, an *earlier* code from the same validity
window is still accepted on a subsequent sign-in. An attacker who observed an earlier
code can keep using it for the rest of its window — including after the legitimate
user has already signed in with a newer code. Accepting a code must invalidate that
code and every earlier one in the window, while a genuine current code must still be
accepted once.

### Turning off the second factor without re-entering the password
In the account-security area, the action that turns off app-based multi-factor
authentication asks only for a current one-time code (or a recovery code); it never
asks the account holder to confirm their current password. Anyone who obtains a live
authenticated session — without knowing the password — can therefore strip the second
factor from the account. Sensitive multi-factor management must require the account's
current password to be re-entered and verified; supplying the correct password (and a
valid code) must still complete the change.

## What must keep working
- Normal sign-in: a valid password presents the challenge; a valid authenticator code
  or a valid recovery code completes authentication; a wrong password is rejected.
- A legitimate file upload on a component that really does expose a file-upload field
  still succeeds.
- The account holder can still turn off app-based multi-factor authentication when
  they supply the required credentials.

## Environment
The repository is checked out at `/app`; all PHP dependencies are already installed.
The verifier exercises these flows through the framework's own PHPUnit / Livewire test
harness backed by an in-memory SQLite database, with no network access. You do not
need to start any web server — the tests boot the framework in-process and drive the
real login, challenge, upload and account-security entry points.
