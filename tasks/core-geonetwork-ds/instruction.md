# GeoNetwork: a sign-in redirect can leave the site

GeoNetwork is a web application for publishing and searching geospatial metadata. People
often reach it through single sign-on: a link takes them to an external identity provider,
and once they have authenticated there the application returns their browser to the page
they were on, using a destination carried in the request.

## Observed impact

A crafted sign-in link carries an off-site destination in its `redirectUrl` query parameter.
After the user completes single sign-on, the application answers with a redirect to
`//attacker.invalid/`; the browser follows it and the user lands on the attacker's site,
even though the parameter is meant to name a page inside GeoNetwork.

## Security property

No value that arrives with a request may cause the application to send the browser to an
address that is not on the configured site. This holds regardless of how the destination
arrives. An off-site destination must never be used to move the browser: the application
must either refuse the request with a client error or fall back to a safe destination of its
own choosing.

A destination is on the site when it is a path on the site, or an absolute address whose
protocol, host and port are the configured site's (the site's default port may be written
out or omitted). An address with a different protocol, host or port is off-site.

## Contracts

- **Refusal.** An off-site destination must never be used. Refusing with a client error and
  falling back to a safe destination are both acceptable outcomes; the response must not
  carry the off-site destination.
- **Return-to-page keeps working.** Returning the user to the page they were on must keep
  working exactly as it does today, including when that page is supplied as an absolute
  address on the configured site.
- **Defaults keep working.** When no destination is supplied, the existing configured
  default behaviour is unchanged.
- **Preservation.** Everything that works today keeps working.
- The examples above are examples, not the full set of values or entry points.

## Constraints

Fix the reported problem and its close variants. Keep legitimate use working. Do not look up
the upstream fix. Do not special-case the example.
