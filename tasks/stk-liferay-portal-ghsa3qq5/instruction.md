# Only redirect to destinations the operator has sanctioned

## The system

Liferay is a portal platform: a Java web application built from portlets, themes and shared
services. After an action — signing in, changing a password, following a link through single
sign-on — the portal commonly sends the browser onward, either back to a page on the portal or to
another site the operator has configured. The portal ships a check that decides whether a
destination may be used: a destination is allowed when it is a path on this site, a host that
belongs to the portal, or a host the operator has listed as an allowed redirect target.

## Observed problem

A link to the portal can carry the destination `///evil.example`. The portal accepts it, even
though a browser treats it as another site, and once the action completes the browser leaves for
that site.

## Security property

The portal must never send a user's browser to a destination the operator has not sanctioned.
Every destination the portal redirects to must first pass the portal's redirect check: it must be
a path on this site, a host that is one of the portal's own domains, or a host the operator has
configured as allowed. A destination that fails the check must produce a client error and must not
be followed.

## Keep working

Everything that works today keeps working exactly as today. In particular, ordinary relative
destinations continue to be accepted unchanged, destinations on hosts the operator has allowed
continue to be accepted, and a redirect for an ordinary relative destination still reaches the
client.

The destination in this report is an example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working exactly as it does today. Do
not look up the upstream fix for this report, and do not special-case the example.
