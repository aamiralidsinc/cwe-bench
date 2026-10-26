# Another web page can read the mailbox

Mailpit is a local mail catcher with a web UI. The UI keeps a live connection to the server so that
every new message appears in the inbox immediately, and the same server exposes the mail interface
that the UI and local scripts use.

A user who keeps the mail UI open visits an unrelated page. That page opens the mail server's live
notification stream and receives the sender and subject of every new message, even though the user
never approved it.

## Requirement

No page served from another origin may read the mailbox's data or change the mailbox through this
server.

A refusal is a client error and has no effect.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
