# LobeChat — server-side fetching of caller-chosen destinations

## What this is

LobeChat is a self-hosted AI chat application. Its web server performs outbound requests on behalf
of the browser: it relays content from addresses named during a conversation, and it sends chat
requests to the model service the deployment is configured to use. Some destinations are chosen by
the operator when the deployment is set up; others arrive from the people using the application.

## Observed problem

A signed-in user can make the server connect to the deployment's own loopback interface. Asking the
server's general-purpose fetch endpoint to retrieve `http://127.0.0.1:<port>/...` returns the answer
of a service that is reachable only from the server itself. The server makes the request from its
own network position instead of the browser's, so the caller sees what the server can see.

## Security property

No destination supplied by a caller may cause the server to connect to an address that is not
globally routable — loopback, link-local, private, unique-local, carrier-grade NAT, or any other
internal range — whether the destination is written as a literal address (including IPv6 forms) or
as a name that resolves to one, and at every hop when a permitted destination redirects.

The rule follows the data, not the request shape: any value a caller can influence that ends up
being fetched is covered, wherever in the request it arrives and however it is carried. A request
that violates the rule is refused with a client error (any 4xx response), and the refused address
is never contacted: nothing internal is read, relayed, stored or forwarded.

## Keep working

Everything that works today keeps working exactly as today. A destination the deployment configured
for itself is not caller-supplied and keeps being used, including when it is private or runs on the
same host. A permitted destination still answers as before: its body and headers are relayed
unchanged, a redirect to another permitted destination is still followed, and content fetched from
a permitted destination is handled exactly as it is today.

The examples above are examples, not the full set of cases.

## Constraints

- Fix the underlying problem and its close variants, not just the one example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
