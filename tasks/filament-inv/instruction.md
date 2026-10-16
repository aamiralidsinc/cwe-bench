# Admin panel sign-in and second-factor security report

## Report

We run admin panels built with the PHP admin-panel framework whose source is in
`/app`. People sign in on a panel's login screen, then pass a second-factor step
(a code from an authenticator app, an emailed code, or a recovery code). They
manage their second factor themselves in the account area of their profile. Each
panel decides which accounts it admits.

A security review of these flows, partly done from outside with nothing but the
requests a browser sends, found that the panel does not keep the properties
below. For example, an anonymous visitor replayed the browser's file-upload
requests against the login screen, which has no file field, and got files staged
in the application's temporary storage. Anyone can fill the server's disk this
way without an account. Treat the example as one symptom. The panel must keep
every property below.

## Security properties the panel must keep

- A screen accepts an uploaded file only into a field it actually offers as a
  file upload. A screen without such a field, the login screen included, never
  takes in a file, for anyone.
- Signing in must not tell someone who has not finished signing in whether a
  password is right for an account that the panel does not admit. For such an
  account the login screen answers exactly as it does to a wrong password,
  whether the password given is right or wrong.
- An authenticator-app code is single-use. Once a code has been accepted for an
  account, neither that code nor any code generated before it may be accepted
  again for that account, in any session.
- Only someone who knows the account's current password may remove its second
  factor. Turning off authenticator-app sign-in requires the current password,
  entered in a `password` field on the turn-off form, as well as the code the
  form asks for today. A signed-in session plus a code is not enough.
- A request that has to be refused is answered as a deliberate client error (for
  example forbidden, or a validation error), not by crashing with a server
  error. It has no effect: nothing is uploaded, signed in or changed.

## What must keep working

- Normal sign-in, exactly as today: a correct password for an admitted account
  leads to the second-factor step, and a valid authenticator code or a valid
  recovery code then completes sign-in. A wrong password is rejected with the
  usual "credentials do not match" error.
- A current authenticator code is still accepted once.
- Uploading a file into a field that really is a file upload works exactly as
  today, from start to finish.
- The account holder can still turn off authenticator-app sign-in by giving
  their current password and a valid code.

## Constraints

- Fix the panel so that the attack above and close variants of it no longer
  work, while legitimate use keeps working.
- Do not modify, delete or add tests. Hidden tests will grade the result.
- Do not look up or copy the upstream fix.
- Do not special-case the example.

## Environment

The repository is checked out at `/app`, and all PHP dependencies are already
installed. You do not need to start a web server. The verifier boots the
framework in-process through its own test harness, with an in-memory SQLite
database and no network access, and drives the real screens.
