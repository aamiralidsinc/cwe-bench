# A preview must never reach a private address

`link-preview-js` turns a link into a preview: it fetches the page behind a URL (or behind the
first URL in a block of text) and reports its title, description, images and other OpenGraph
data. A server that previews links supplied by its users can give the library an
address-resolution hook, so that a link pointing into the server's own network can be refused.

## What we see

A user submits a link and the server supplies that hook. The hook reports a public address, so the
preview is allowed. By the time the request is made the name answers with a private address
instead, and the response the user gets back is the page of a service that exists only inside the
server's network.

## The rule

No request a preview makes may open a connection to an address that is not public. The hook
decides that: a link whose reported address is not public is refused before anything is
requested, and a request that is made goes to the address that was reported and to no other.

Refusing means the returned promise rejects with an error, with nothing requested. Everything that
works today keeps working exactly as today, and the hook stays optional: a caller that supplies no
hook must not be forced to start. The link above is one example, not the full set of forms a link
or an answer can take.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the published
fix for this issue, and do not special-case the example.
