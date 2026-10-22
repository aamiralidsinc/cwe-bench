# Any website can use the local Nhost configuration service

The Nhost CLI (`nhost dev up`) runs a local development stack for a project. Part of
that stack is a small configuration service that the local Nhost dashboard calls to
read and edit the project's configuration (`nhost/nhost.toml`) and secrets
(`.secrets`), and to look at service logs. It serves GraphQL at
`/v1/configserver/graphql` and `/v1/logs/graphql`, behind the dashboard's host (for
example `https://local.dashboard.local.nhost.run/v1/configserver/graphql`).

## What happens

While `nhost dev up` is running, any web page the developer opens can use this service
from their browser. For example, a page on `https://evil.example` can `fetch()` a
GraphQL query for the project's secrets from the service, read the admin secret, JWT
key and every other stored secret in the response, and send changes to the
configuration and secrets the same way.

## Required behaviour

- **Browser access is for the dashboard only.** A web page may make CORS-preflighted
  requests to the service or read its responses only if it comes from an origin the
  local dashboard is served from: `<subdomain>.dashboard.local.nhost.run`, where
  `<subdomain>` is a single DNS label (the project's subdomain, `local` by default), or
  `local.dashboard.nhost.run`, over `http` or `https`, with or without a port. No other
  origin may, however closely it resembles one of these. That includes other hosts and
  local development servers on the developer's machine.
- **Secret values never leave the service.** No response from the service may contain a
  secret value it read from the project's secrets file. This holds for the dashboard and
  every other client. Secret names stay visible.

When an origin is refused, the service must not grant it in its CORS answer. It may
also reject the request with a client error. Either way, a refused request must have no
side effect. The origins and queries above are examples, not the full set of cases the
rules cover.

## Must keep working

- The dashboard on its origins works exactly as today. That covers browsing the
  configuration (including the configured service versions and settings) and editing it
  without losing its `{{ secrets.NAME }}` references. It also covers listing secret names,
  adding, changing and deleting secrets, and using the logs API. The dashboard's existing
  queries and mutations keep succeeding, including reading the configuration with its
  secrets filled in.
- Adding, changing or deleting one secret from the dashboard leaves the other secrets as
  they are.
- Clients that send no `Origin` header, such as command-line tools and scripts, keep
  working as today, apart from the secret-value rule above.

## Constraints

- Fix the problem and its close variants, not just the example above.
- Keep legitimate use working.
- Do not weaken or delete tests. Existing tests that assert the old, insecure behaviour
  may be updated.
- Do not look up the upstream fix.
- Do not special-case the example origin or query.
