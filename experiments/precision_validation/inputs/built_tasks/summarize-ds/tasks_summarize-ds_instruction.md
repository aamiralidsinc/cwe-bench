# Summarized content can reach internal network services

## What this is

This project turns a link into readable text and a summary. It can be used directly by a caller and
also runs as a background service. While processing a link it may retrieve further material that
the link or the content it names points to.

## What was observed

When a user summarizes a link whose retrieved material names another address, the process opens a
connection to that address even when it is not reachable from the public internet. When the response
can be parsed, the non-public content is returned to the user as part of the result. The same
connection is opened when the address the user supplied is itself written in a form that denotes
such a destination.

## Required property

No connection the product opens in the course of summarizing may target anything other than a
public internet destination. This applies to the address the product was asked to summarize and to
every address named by the material it retrieves, and it holds however that address is supplied: as
a literal in any accepted IPv4 or IPv6 form, including a form whose value embeds an IPv4 address; as
a name whose resolution yields such an address; or at any hop of a redirect chain. The decision must
be made on the destination the connection would actually use, after name resolution and after any
redirect — not on the text that was supplied.

Loopback, private, link-local, carrier-grade-NAT, multicast, documentation, and other non-public
ranges are not public internet destinations.

A refused connection must happen before the connection is opened and must be visible: an error or an
absent optional result where the product is used directly, and a client error (4xx) where the
product runs as a service. A refusal must never be reported as success.

Legitimate use must keep working exactly as today. Public host names, public IP literals, including
IPv6 forms whose embedded address is public, and redirect chains that stay on public destinations
must still be fetched, and everything the product derives from them must keep working.

The observed case is one instance, not the full set: the property applies to every destination the
product would connect to in the course of summarizing.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not modify or add tests. Do
not look up the upstream fix or advisory. Do not special-case the example input.
