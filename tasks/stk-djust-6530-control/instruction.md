# A refused live view must not keep receiving events

djust is a Django framework for reactive, server-rendered pages. An application
declares a view class; the framework authenticates the mount, sends the rendered
markup to the browser, and then runs the view's named event handlers on the
server as the user interacts, updating the page over the same session.

## Reported problem

A view that requires a signed-in user can still be driven by a client that never
signed in. Mount such a view while signed out: the server tells the client to go
to the login page, but the session stays usable, and an event sent afterwards
still runs the view's handler and changes state. A browser that follows the
redirect hides this; any other client reproduces it. For example: open a session,
mount a view declared as requiring a signed-in user, ignore the redirect, and
send one of its events — the handler runs.

## Required behaviour

A live session may run a view's event handlers only for a view whose mount
completed and whose authorisation check passed.

Everything that works today must keep working exactly as today.

A client whose mount was refused must not get a successful result for an event
aimed at that view, and no handler may run as a side effect.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working.
- Do not look up the upstream fix, the advisory, or any patch for this issue.
- Do not special-case the example.
