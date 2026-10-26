# Credentials must not follow a redirect to another origin

This repository implements the TypeScript HTTP request layer that generated API clients use. A
request adapter authenticates each outgoing request, runs a middleware pipeline, follows
redirects, and returns the response. Applications configure it with an authentication provider
that supplies a bearer token, and they may attach their own request headers, including cookies and
proxy credentials.

## Observed impact

A client built with a bearer-token provider calls `https://api.example.com/v1/me`. The server
answers `302` with `Location: https://collector.example/ingest`. The request that the library then
sends to `collector.example` still carries the caller's `Authorization: Bearer …` and
`Cookie: session=…`. Anyone who can answer for a trusted endpoint, or make it redirect to another
origin, receives the caller's credentials.

## Required property

A request that carries a credential the caller attached for the addressed origin must not be able
to reach any other origin — a different host (including port) or a different scheme — however the
credential header name is spelled, and including when a redirect points elsewhere.

The credentials in scope are the standard request credential headers: `Authorization`, `Cookie`,
and `Proxy-Authorization`.

## Contracts

- A redirect to a different origin must still complete: the request is sent without the credential
  headers and its response is returned as today, and non-credential headers are untouched.
- A redirect that stays on the same host and scheme, including a relative redirect, must keep
  every request header exactly as it is today.
- A caller-supplied callback that decides which headers to remove on a redirect must still be used
  and must still be able to keep headers.
- Everything that works today keeps working exactly as today.

The example above is one instance; the requirement applies to every request, not only the one
shown.

## Constraints

- Fix the problem and its close variants, not only the example.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
