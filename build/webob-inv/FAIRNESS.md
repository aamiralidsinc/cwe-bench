# webob-inv: fairness of the rewritten instruction

All tests drive the request at `http://localhost/app/page`. Security tests pass when the resulting
location is not `None` and its host (by `urlsplit`) is `localhost` or empty.

Abbreviations: **P1** = "A target or reference counts as an explicit absolute URL ... or an explicit
protocol-relative reference ... only if it is one as given, from its first character." **P2** = "Any
other value must end up on the request's own host when the library makes it absolute against the
request. This applies whatever characters the value begins with or contains, and on every route by
which the library produces a redirect location or resolves a reference against the request. Such a
value is still turned into a URL (it is not rejected or dropped), but that URL must not name another
host."

## Security tests (`tests/security/test_open_redirect.py`)

| Test | What it asserts | Sentence that makes it fair | Risk |
|---|---|---|---|
| `test_response_leading_space_protocol_relative` | Response with Location ` //evil.example/x`, run as WSGI app, stays on localhost | Trigger example (the same value, leading space), P1 and P2 | low |
| `test_response_leading_c0_control_protocol_relative` | Same with `\x01//evil.example/x` | P1 (it is not protocol-relative "from its first character") and P2 ("whatever characters the value begins with") | low |
| `test_response_leading_space_before_scheme` | Same with ` https://evil.example/x` | P1 (with the leading space, it is not an absolute URL as given) and P2 | low. P1 is the needed contract: browsers strip leading spaces, so without P1 a reader could treat this value as a deliberate absolute URL |
| `test_exception_leading_space_protocol_relative` | Built-in redirect exception (HTTPFound) called as a WSGI app with ` //evil.example/x` stays on localhost | P2 ("on every route by which the library produces a redirect location"), and the trigger example | low |
| `test_exception_leading_tab_protocol_relative` | Same with `\t//evil.example/x` | P1 and P2 ("whatever characters the value begins with") | low |
| `test_exception_leading_space_before_scheme` | Same with ` https://evil.example/x` | P1 and P2 | low |
| `test_relative_url_leading_space_protocol_relative` | `Request.relative_url(' //evil.example/x')` stays on localhost | Report ("ask the library to turn a link reference into a full URL against the page currently being served") and P2 ("or resolves a reference against the request") | low-medium: this route is a URL helper, not a redirect, so the report has to name it at product level. It does so without naming the function |
| `test_relative_url_leading_c0_control_protocol_relative` | Same with `\x01//evil.example/x` | As above, plus P1 | low-medium (same reason) |
| `test_relative_url_leading_space_before_scheme` | Same with ` https://evil.example/x` | As above, plus P1 | low-medium (same reason) |

All security tests also need a non-`None` location, and `relative_url` must not raise. This is covered
by P2: "Such a value is still turned into a URL (it is not rejected or dropped)".

## Functional tests (`tests/functional/test_redirect_feature.py`)

| Test | What it asserts | Sentence that makes it fair | Risk |
|---|---|---|---|
| `test_response_absolute_offsite_url_is_preserved` | Location `https://other.example.com/landing` keeps host `other.example.com` and scheme `https` | "An explicit absolute URL to another host (an identity provider, a payment page, a CDN) still reaches that host with its scheme." | low |
| `test_response_absolute_same_host_path` | Location `/dashboard` becomes host localhost, path `/dashboard` | "Site-absolute paths ... still resolve against the request as before." Also standard URL resolution | low |
| `test_response_relative_reference_resolves_under_current_dir` | Location `page2` becomes localhost `/app/page2` | "relative references ... resolved against the current page" "as before". Also standard RFC 3986 resolution | low |
| `test_response_protocol_relative_stays_on_host` | Location `//cdn.example.com/asset.js` is kept on localhost, and `cdn.example.com` stays in the URL | "Explicit protocol-relative references are outside this report. Leave their handling as it is today." Today this path already keeps it on-host with the text in the path | low |
| `test_exception_absolute_offsite_url_is_preserved` | Exception with `https://sso.example.org/auth` keeps that host and `https` | The absolute-URL preservation bullet (it names an identity provider) | low |
| `test_exception_relative_location_resolves_on_host` | Exception with `/login` becomes localhost `/login` | The site-absolute paths bullet | low |
| `test_relative_url_resolves_under_current_dir` | `relative_url('other')` gives localhost `/app/other` | "relative references resolved against the current page" "as before" | low |
| `test_relative_url_to_application_root` | `relative_url('sub', to_application=True)` gives localhost `/sub` | "... and those resolved against the application root" "as before" | low |
| `test_relative_url_explicit_protocol_relative_unchanged` | `relative_url('//other.example.com/x')` still gives host `other.example.com`, path `/x` (today's behaviour) | "Explicit protocol-relative references are outside this report. Leave their handling as it is today." The agent can check today's result by running the unmodified code | low-medium: a security-minded agent may want to fold it anyway. The sentence forbids that plainly |

## Note on scope

The "leave their handling as it is today" clause is slightly broader than the tests. On the redirect
exception route, a bare `//host` is sent off-site today, and no test checks that route either way. If an
agent follows the clause, it passes. If it tightens that route, it also passes. So the clause adds no
requirement that could fail a correct fix. The old instruction made the same exclusion ("not an
explicitly protocol-relative reference").

## Details removed from the old instruction

- The three entry points by name: setting the `Location` header on a response object, the library's
  "built-in HTTP redirect exceptions", and asking the library "to resolve a target reference relative to
  the current request URL". They are now one product-level clause ("every route by which the library
  produces a redirect location or resolves a reference against the request") plus the report's mention
  of turning a link reference into a full URL.
- The mechanism: "the library turns the target into an absolute URL by combining it with the address of
  the incoming request", and "the leading character is discarded while the target is being resolved,
  and the remainder is parsed as a foreign host".
- The character classes: "an ASCII space or a non-printing C0 control character".
- The extra variant spellings: the leading control byte `\x01`, and "a leading space in front of an
  absolute `https://…` target".
- "The same value reaches the same outcome through each of the redirect-producing APIs described above,
  including the ones that resolve a reference relative to the request". This hinted that there are
  several sites and that the obvious one is not enough.
- "Not only the most obvious one" (a hint that more than one site is affected).
- The reasoning about why the application trusts the value ("it is not an absolute URL and it does not
  begin with the protocol-relative `//` marker"). The contract part of this is kept, in neutral words, as P1.
- "Leading spaces or control characters must not be usable to ..." is now covered by "whatever
  characters the value begins with or contains".
- "WSGI library" is kept, but nothing names the package, the module, a class or a function.

## Added

- A standard constraints block. The old instruction had none.
- `/app` as the repository location, in Environment. The Dockerfile uses WORKDIR `/app` and installs it
  in editable mode.
