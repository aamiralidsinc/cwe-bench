Astro is a web framework. For sites rendered on demand (server output), Astro's origin check (`security.checkOrigin`, on by default) is meant to stop cross-site request forgery. A form submission that comes from another site must never reach the site's Astro Actions, API endpoints or pages. Besides the batteries-included request handling, Astro offers composable request-handling building blocks. A site can assemble its own server from them, for example with Astro's Hono integration (`astro/hono`).

## Observed impact

A site serves its pages from a Hono app that mounts `actions()` before `middleware()`, as the advanced-routing example does. It defines a form action `deleteAccount`. A page on another origin auto-submits an HTML form to `POST https://site.example/_actions/deleteAccount` with an `application/x-www-form-urlencoded` body. The victim's browser sends the request and the action runs. The account is deleted, although the origin check is enabled.

## Required behaviour

While the origin check is enabled, these invariants hold for every on-demand route:

- No request can cause any of the site's actions, endpoints or pages to run if the standard request handling's origin check would refuse it.
- This covers every way an action can be invoked. It holds for every way a site can assemble its server from Astro's building blocks.
- Such a request gets a client error (4xx) response, and no action, endpoint or page handler runs. Crashing, or answering with a server error, is not a refusal.

Legitimate use must keep working exactly as today:

- same-origin submissions of any kind reach actions, endpoints and pages;
- cross-site requests with a non-form content type, such as `application/json` RPC or API calls, are unaffected;
- `GET`, `HEAD` and `OPTIONS` requests are unaffected;
- with `security.checkOrigin: false`, no origin check happens anywhere;
- the standard request handling keeps its current behaviour.

The request above is one example, not the full set of affected requests.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example (its action name, path or origin).
- There is no network access.
