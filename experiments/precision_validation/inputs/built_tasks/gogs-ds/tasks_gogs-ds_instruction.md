# Time-limited account codes outlive their configured lifetime and cross purposes

## System

This project is a self-hostable Git service. Accounts are created with a user
name, an address and a password. Some account actions are authorized by a
time-limited code that the server sends to the account's address; when
confirmation is required, the account stays inactive until that action is
completed. A deployment configures, independently for each purpose, how long a
code issued for that purpose lives.

## Observed impact

With the lifetime configured for one purpose set to one minute, a code issued
for that purpose still completes its action when it is used two minutes later.
Separately, a code issued for one account action is accepted as authorization
for a different account action. In both cases the server applies the change the
code authorizes to the account that the code was issued for.

## Security property that must hold

A time-limited code may be accepted only to complete the single account action
it was issued for, and only while the lifetime configured for that action is
still running. This holds wherever the server issues such a code and wherever
it accepts one.

## Contracts the fix must honor

- **Refusal form.** A code that has expired, or that was issued for a different
  action, is refused with a client error (a 4xx response) and leaves the
  account unchanged; it is not a server error, and it changes no password and
  no account state.
- **Preservation.** These keep working exactly as today:
  - completing an account action with a code issued for it while the lifetime
    configured for that action is still running, through every interface the
    product offers;
  - codes issued for other actions keep working for their own action within
    their own configured lifetime;
  - the check that tells a caller whether a code is usable still reports a
    fresh, valid code of the expected purpose as usable;
  - sign-up, sign-in and account confirmation otherwise unchanged.
- **Tests.** The repository's existing tests must compile and pass without being
  modified.

The example above is one instance, not the full set of ways the properties can
be violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example values.
- Do not consult any upstream advisory or fix for this issue.
