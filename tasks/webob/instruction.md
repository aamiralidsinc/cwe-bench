# Redirects can be steered to an attacker-controlled host

## Summary

A web application built on this WSGI library issues redirects in the usual
ways: it sets the `Location` header on a redirect response object, it returns
the library's built-in HTTP redirect exceptions, and it asks the library to
resolve a target reference relative to the current request URL. In each case
the library turns the target into an absolute URL by combining it with the
address of the incoming request, and the application relies on that step to
keep an application-supplied, non-absolute target pointing at its own site.

That guarantee does not hold. A target string that begins with an otherwise
insignificant leading character — an ASCII space or a non-printing C0 control
character — followed by text that looks like a host reference is silently
rewritten into a URL that points at a **different, attacker-chosen host**.

## How it is triggered

Consider an application running at `http://localhost/app/page`. A victim is
given a link whose redirect-target parameter is set to a value such as:

```
 //attacker.example/phish
```

(note the single leading space), or the same thing with a leading control byte
such as `\x01`, or a leading space in front of an absolute `https://…` target.
The application treats this as a harmless relative reference — it is not an
absolute URL and it does not begin with the protocol-relative `//` marker — and
hands it to the library to be made absolute against the request URL. The
browser-visible result is a redirect to `http://attacker.example/phish`: the
leading character is discarded while the target is being resolved, and the
remainder is parsed as a foreign host. The same value reaches the same outcome
through each of the redirect-producing APIs described above, including the
ones that resolve a reference relative to the request. This enables phishing
and credential theft against users who trust the original site.

## What a correct fix must achieve

- A redirect/resolution target that the application would regard as same-site
  (one that is not an explicitly absolute URL and is not an explicitly
  protocol-relative reference) must still resolve onto the **request's own
  host** after being made absolute. Leading spaces or control characters must
  not be usable to turn such a target into a redirect to another host, and this
  must hold for every way the application can produce or resolve a redirect
  target, not only the most obvious one.
- Legitimate behaviour must be preserved: an application that deliberately
  redirects to an absolute URL on another host (for example an identity
  provider or a CDN) must still reach that host; an absolute same-site path
  must still resolve on the request host; and a reference resolved relative to
  the current request must resolve exactly as it does today.

## Environment

Pure Python; no services to start. The library is installed in editable mode,
so edits under the source tree take effect immediately.
