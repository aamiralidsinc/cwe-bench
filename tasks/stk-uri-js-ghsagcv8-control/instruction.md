# URL host spoofing

This project is a JavaScript library for reading and rewriting URLs. Applications rely on it to
decide which host a URL points at — for example, a link checker that only follows URLs whose host
is on an allowlist, or a service that forwards a request to the host it was given.

Reading the host of `http:evil.example/account` yields nothing, so an application that checks that
host against its allowlist sees no host to match and lets the link through, while a browser opens
the URL at `evil.example`.

## Required property

For any URL string that a browser would resolve to a particular host, the library must report that
same host — the host the browser would actually contact. A URL that a browser would resolve to a
host must never be reported without that host.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today, apart from gaining the host
described above.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
