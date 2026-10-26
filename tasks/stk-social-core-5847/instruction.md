# A stored sign-in flow can be continued by another browser session

Python Social Auth Core is a library that web applications use to sign people in through external
providers. A sign-in can pause partway so the application can collect something else from the user;
the library stores the halted flow and gives the application a token that identifies it. When the
browser comes back to the completion endpoint, the application asks the library to continue the
stored flow.

Our application uses the library this way. A visitor who reaches the completion endpoint with a
token for a sign-in flow that was started in someone else's browser session is signed in as that
other account. The visitor's own session continues a flow it never started, which is a login
cross-site request forgery: the visitor is silently signed in to an account the attacker controls.

## Security invariant

A stored sign-in flow may be continued only by the browser session that started it. No value
supplied by a request may make a session continue a flow that the session did not start, and no
such request may sign anyone in.

## Refusal

A refused request gets a client error: the library's authentication error or a refusal response,
never a crash. It must not continue the stored flow, run any of its steps, or sign anyone in.

## What must keep working

Everything that works today keeps working exactly as it does today: ordinary sign-ins, a flow
continued by the session that started it, every way the library already accepts a flow's
identifier, and flows the library itself sets up to be completed outside the starting session.

The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
