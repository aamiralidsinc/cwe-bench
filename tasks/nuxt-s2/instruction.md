# Route rules can be bypassed by changing the letter case of a URL

This is the source of a Nuxt site framework. A site built with it can attach route rules to
paths: a rule can put a page behind a sign-in check, send the browser somewhere else, choose
how a page is rendered, or decide that it should be prepared ahead of time.

Visitors can reach a page that should be behind the sign-in check by requesting the same route
with different capitalisation. With a rule written for `/Admin/Dashboard`, for example, a
request to `/ADMIN/DASHBOARD` is served and the configured check never runs.

## What must hold

A route rule belongs to the route it names, not to the spelling that was used to configure it.
Every request that resolves to that route must receive that rule with its configured values, and
no request that resolves to a different route may receive it. This holds for every decision the
framework takes from those rules, and a rule's configured values are preserved wherever they are
used (a redirect target, for example, keeps the value the site wrote).

Routing is case-insensitive by default, so letter case is not part of a route's identity: the
rules written for a route apply to every capitalisation of it, and a request is never served
without a rule that a site configured for it. When a site enables case-sensitive route matching,
letter case does become part of the identity: a rule binds only to the capitalisation it was
written with, and two rules that differ only in case remain two different rules.

The framework's public lookup that returns the rules for a path keeps every argument form it
accepts today and keeps returning the same values it returns today for paths that already match.
Everything that works today keeps working exactly as it does today.

The examples above are examples, not the whole set.

## Constraints

- Fix the problem and close its variants; do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up the advisory or the upstream fix.
