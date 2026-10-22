# Clients can impersonate other users through header-name spellings

The repository in `/app` is Traefik, an HTTP reverse proxy. Traefik can set, replace or remove
request headers before a request is forwarded to the backend. For example, basic authentication can
pass the authenticated user's name to the backend in a header.

## Observed impact

A router uses basic authentication configured to pass the user name to the backend in the
`X-Auth-User` header, in front of a PHP application. Alice logs in with her own valid password and
adds the request header `X_Auth_User: admin`. Traefik puts `alice` into `X-Auth-User`, but it also
forwards `X_Auth_User` unchanged. PHP, like CGI, WSGI and many other backends, ignores letter case
and reads `_` and `-` in header names as the same character. It therefore sees `admin` as the
authenticated user.

## Required behaviour

- Whenever Traefik sets, replaces or removes a request header before forwarding the request, no
  header sent by the client may reach the backend under a name that differs from that header's name
  only in letter case or in `_` versus `-`. This applies whichever feature or configuration
  manages the header, and with every entry-point setting, including the default. It does not extend
  to the hop-by-hop headers (such as `Connection`) that every HTTP proxy drops.
- Refusing such a request with a client error (4xx), without forwarding it, is also acceptable.
- Operators also need a blanket control. Add the entry-point option `http.underscoreHeadersStrategy`
  to the static configuration (for example `--entryPoints.web.http.underscoreHeadersStrategy=delete`,
  or `underscoreHeadersStrategy` under `entryPoints.<name>.http` in the configuration file). It takes
  these values:
  - `keep`, the default (also when the option is unset): headers with underscores in their names are
    forwarded as today, subject to the first rule above;
  - `delete`: every request header whose name contains `_` is removed before routing, and all other
    headers, including several values of one header, are forwarded unchanged;
  - `reject`: a request carrying any header whose name contains `_` is refused with a client error
    and never routed, and other requests are served normally.

  Any other value is a configuration error: the entry point must fail to start.

## Must keep working

- Headers that Traefik does not set or remove, including names with underscores, are forwarded
  exactly as today unless `delete` or `reject` is chosen.
- The headers Traefik sets itself, such as the authenticated user's name, keep their names and
  values as today.
- Authentication, header configuration and routing otherwise work exactly as today.

The names and values above are examples, not the full set of cases that must be handled.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not modify or add tests. Do
not look up the upstream fix. Do not special-case the example.
