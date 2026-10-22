# Clients can impersonate a user through a header-name spelling

The repository in `/app` is Traefik, an HTTP reverse proxy. Before forwarding a request to a
backend, Traefik can set, replace or remove request headers, including headers that carry values
the proxy itself vouches for.

## Observed impact

A client can add a request header under a spelling that the receiving application reads as the
same header: letter case is ignored, and `_` is read as `-` by common PHP, CGI and WSGI backends.
When the proxy manages that same header under another spelling, the application reads the
client's value in place of the value the proxy set, so the client is trusted for data the proxy
vouched for.

## Required behaviour

- Whenever Traefik sets, replaces or removes a request header before forwarding the request, no
  header sent by the client may reach the backend under a name that differs from that header's
  name only in letter case or in `_` versus `-`. This holds whichever feature performs the
  operation and with every entry-point setting, including the default. Refusing such a request
  with a client error (4xx), without forwarding it, is also acceptable. The hop-by-hop headers
  that every HTTP proxy drops are out of scope.
- The same equivalence applies to operator-configured header selection: a header name or a
  header-selecting pattern written with dashes and one written with underscores select the same
  headers.
- Add the entry-point HTTP option `underscoreHeadersStrategy` (for example
  `--entryPoints.web.http.underscoreHeadersStrategy=delete`, or `underscoreHeadersStrategy` under
  an entry point's `http` settings in the configuration file). It takes these values:
  - `keep`, the default (also when the option is unset): headers with underscores in their names
    are forwarded as today, subject to the first rule;
  - `delete`: every request header whose name contains `_` is removed before routing, and all
    other headers, including several values of one header, are forwarded unchanged and in order;
  - `reject`: a request carrying any header whose name contains `_` is refused with a client
    error and never routed, and other requests are served normally.

  Any other value is a configuration error: the entry point must fail to start.

## Must keep working

- Headers that Traefik does not set or remove, including names with underscores, are forwarded
  exactly as today unless `delete` or `reject` is chosen.
- The headers Traefik sets itself keep the names and values configured for them, and a legitimate
  request carrying several values of one header is still served.
- Existing behaviour otherwise works exactly as today.

The equivalences above are illustrative; they are not the full set of cases that must be handled.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not modify or add tests.
Do not look up the upstream fix. Do not special-case the example.
