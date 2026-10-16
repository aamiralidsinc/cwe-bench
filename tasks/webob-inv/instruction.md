# Redirects can be steered to an attacker-controlled host

## Report

Our web applications are built on the Python WSGI request/response library
checked out at `/app`. They send users on with redirects, and they also ask the
library to turn a link reference into a full URL against the page currently
being served. When the application passes a target that is not itself a full
URL, it relies on the library to make it absolute on the site's own host.

A penetration test found that this does not always hold. With an application
served at `http://localhost/app/page`, a crafted value in a "return to"
parameter, ` //attacker.example/phish` (note the single leading space), was
passed on by the application as a harmless same-site target. The browser was
then sent to `http://attacker.example/phish`. This allows phishing and
credential theft against users who trust our site.

## Security properties the library must keep

- A target or reference counts as an explicit absolute URL (with a scheme such
  as `https:`) or an explicit protocol-relative reference (starting with `//`)
  only if it is one as given, from its first character.
- Any other value must end up on the request's own host when the library makes
  it absolute against the request. This applies whatever characters the value
  begins with or contains, and on every route by which the library produces a
  redirect location or resolves a reference against the request. Such a value
  is still turned into a URL (it is not rejected or dropped), but that URL must
  not name another host.
- Legitimate use must keep working exactly as it does today:
  - An explicit absolute URL to another host (an identity provider, a payment
    page, a CDN) still reaches that host with its scheme.
  - Site-absolute paths and relative references still resolve against the
    request as before. This includes relative references resolved against the
    current page and those resolved against the application root.
  - Explicit protocol-relative references are outside this report. Leave their
    handling as it is today.

## Constraints

- Fix the library so that the reported attack and close variants of it no
  longer work, while the legitimate uses above keep working.
- Do not modify, delete or add tests. Hidden tests will grade the result.
- Do not look up or copy the upstream fix for this issue.
- Do not special-case the example value or the host above.

## Environment

Pure Python; no services to start. The library is installed in editable mode
from `/app`, so edits to its source take effect immediately.
