# Remote content reads can reach internal services and forward credentials

CrewAI Tools is a Python library of tools that agents use to read remote content. A caller gives a
tool or a search helper a web address; the product fetches it, follows whatever redirects the site
sends, and returns the page text (or indexes it for a search). Callers can attach their own
credentials — an authorization header, a cookie, an API key, a token — to those reads.

## Observed impact

A caller asks the web-page scraping tool to read `https://example.com/report`. That public site
answers with a temporary redirect to `http://10.0.0.5/admin`; the tool follows it and returns the
internal page's content to the caller. In the same way, when a public site redirects to another
site, an API key or cookie attached to the read is sent along to that other site.

## What must hold

1. Reading a remote resource must never send a request to an internal or otherwise non-public
   network destination. This covers the address the caller gives and every address reached while
   satisfying that read, however that address is chosen. If a read would reach such a destination,
   it must fail with an error and no request may be sent to that destination.

2. Credentials attached to a read must only be sent to a destination that has the same scheme, host
   and port as the address the read started at. Within that same origin they must keep being sent.

These properties apply to every way the product reads remote content, not only the example above.
The example is an example, not the full set of routes or input forms.

## What must keep working

- Public destinations and public redirects, including relative redirects and chains of several
  hops, keep returning content.
- A redirect inside one origin keeps its credentials.
- The existing `CREWAI_TOOLS_ALLOW_UNSAFE_PATHS` opt-out keeps disabling these checks when it is set.
- Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up or copy the
upstream fix. Do not special-case the examples above.
