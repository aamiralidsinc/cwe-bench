# One visitor can make another visitor's browser run code

AVideo is a video and live-streaming platform. Its live pages stay in sync through a
socket service: every open page holds a short-lived connection token issued to whoever
loads the page, and the service relays small JSON frames between connected pages.

A visitor who never signs in can take the token a public page hands out, open a
connection, and relay a frame that makes other viewers' pages run a script of the
sender's choosing, with no click or other interaction from the victim. We reproduced
this from an ordinary browser connection: a second, unrelated viewer's page executed the
script the first visitor supplied.

## The properties we need

**1. No code from a visitor runs in another visitor's page.** Nothing a visitor's browser
supplies to the service may make any other page run code of the visitor's choosing.

**2. What a page shows about who sent something must be true.** Any sender identity or
attribution a receiving page displays must be the one the service established from the
sender's authenticated session, never anything the sender supplied.

## What must keep working

Everything that works today keeps working, including:

- Ordinary frames between visitors still arrive intact.
- A frame carrying something that must not be relayed still has the rest of its content
  delivered, and the connection stays open.
- Notices the platform's own server code sends still reach the recipient and still take
  the effect they take today.

The examples above are examples, not the full set. Fix the problem and its close
variants; keep legitimate use working exactly as today; do not look up the upstream fix;
do not special-case the example.
