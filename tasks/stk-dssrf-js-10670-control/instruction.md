# dssrf: a URL is approved while the request reaches an internal host

`dssrf` is a Node.js library that applications use to decide whether a user-supplied URL is safe to
fetch. A caller passes a URL to one of the library's public checks and, when the answer is safe,
fetches the same URL with an ordinary HTTP client. A safe answer is the caller's assurance that the
request cannot reach a host the deployment treats as internal.

## Observed impact

A caller asks the library about `http://user@localhost/`, receives a safe answer, and then fetches
that same string. The request reaches the local host, which the deployment treats as internal. The
library approved a URL that leads to an internal service.

## Required property

No URL may be reported safe when the request that a caller would make for it could reach a host the
deployment treats as internal. The answer must describe the URL as it will actually be requested.
This holds for every public decision the library exposes about whether a URL may be fetched.

## Contracts

- An unacceptable URL must come back as not safe. The library has no partial or warning answer: its
  public checks answer with a boolean.
- Everything that works today must keep working. A URL that is accepted today and does not lead to
  an internal host must still be accepted, and every helper the library exports today must remain
  available and behave as it does now.
- The fix must work with the dependencies already present in the environment; it runs offline.

Examples in this report are examples, not the full set of shapes that must be handled.

## Constraints

- Fix the reported problem and its close variants; do not special-case the example.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- Do not change or remove the library's public API.
