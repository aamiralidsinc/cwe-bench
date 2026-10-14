# webob — build notes

## What I verified against the real code (not the reader's notes)

- **Flaw, confirmed.** At the vulnerable parent commit `54c1133`, on CPython
  3.11, a redirect target beginning with a stripped-away leading character
  (ASCII space, C0 control, tab) is rewritten to an attacker host when the
  library makes it absolute. Reproduced through three public entry points.

- **Three call sites, confirmed** (the reader guessed 3 + a new util helper):
  1. `Response._make_location_absolute` (the `Location` header path). At the
     parent it strips `\t\r\n` and guards `scheme:` / leading `//`, then calls
     `urllib.parse.urljoin`, which strips *leading space / C0 control* — so
     ` //host` and `\x01//host` and ` https://host` slip through.
  2. The `_HTTPMove`-based HTTP redirect exceptions' WSGI `__call__` — at the
     parent this calls `urllib.parse.urljoin` **directly with no scheme/`//`
     guard at all**, so even a bare `//host` redirects off-site here. (It then
     passes through `_make_location_absolute` via `Response.__call__`, which
     returns an already-absolute off-host URL unchanged.)
  3. `Request.relative_url` — calls `urllib.parse.urljoin` directly.
  The upstream fix replaces the stdlib join with its own RFC-3986 `urljoin` in
  `util.py` and routes all three sites through it.

- **Tempting wrong fix, confirmed and used as the `security_fail` patch.**
  `shallow_strip_one_site.patch` strips leading C0/space in the `Location`
  path only. It leaves the exception path and the relative-resolution path
  exposed, and it is *still* wrong even on the Location path for the
  ` https://host` variant: stripping turns that into an absolute URL the
  scheme guard then trusts. 8 of 10 security tests still fail; all functional
  pass.

- **A `//host`-on-`relative_url` value is NOT part of the vuln.** The upstream
  fix (correctly, per RFC 3986) still resolves a bare protocol-relative
  reference to that host through `relative_url`. So I did not assert anything
  about bare `//` on the relative-resolution path — only the
  whitespace/control-smuggling variants, which the fix does neutralise there.

## Test design

- 10 security tests across the 3 entry points × {leading space, leading C0
  control, leading tab, bare `//` (exception path only), leading space before
  scheme}. Each asserts the browser-visible target stays on the request host.
- 8 functional tests: absolute off-site URL preserved (Response + exception),
  absolute same-site path, relative resolution under the current dir,
  protocol-relative value kept on-host, `to_application` resolution.
- Assertions are property-based (host must not be the attacker host / must be
  the request host), not exact-string, so an independent correct fix also
  scores 1.0 — proven by `alt_percent_encode.patch` (a different-layer fix
  that percent-encodes leading strippable characters and routes all three
  sites through one helper): 18/18.
- `force_same_host.patch` (functional_fail) forces every resolved redirect
  back onto the request host, which kills the legitimate off-site-redirect
  feature: 3 functional tests fail.

## Could not fully verify / caveats

- Only ran the gate's logic locally with pytest from source on CPython 3.11
  before the Docker gate; the authoritative result is the gate run itself.
- The flaw is Python-version dependent (needs the 3.10+ url-join stripping),
  which is why the image pins `python:3.11-slim`. On 3.9 the exploit does not
  reproduce.
