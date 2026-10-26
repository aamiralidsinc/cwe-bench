# Configured credentials are returned by the unauthenticated monitoring API

## System

Glances is a system-monitoring service. Operators configure it through a
configuration file and command-line options: the endpoints it polls, database and
message-broker connections, and the logins and passwords that go with them. It
serves a read-only HTTP API, and a web UI built on that API, to anyone who can
reach it. When no password is configured for the service itself, the API is
reachable without authentication.

## Observed impact

An unauthenticated client can read credentials that were configured for the service.
For example, with

```
[ip]
public_username = operator
public_password = s3cr3t
```

a request to

```
GET /api/4/config
```

returns `public_password` masked but `public_username` in clear. The same response
also carries the configured polling address, including any user information embedded
in it.

## Security properties that must hold

- No credential configured for the service — a password, a login name, an access
  token, or credentials embedded inside a configured address — may appear in any
  response the service returns without authentication. This holds for every response
  and for every way the value is stored or represented: a single value, one element
  of a list, or a value nested inside another value.
- Hiding a credential must not change the value the service itself uses, and must not
  turn a working response into an error.

## Contracts the fix must honor

- **Hidden form.** A hidden value stays represented the way it is today: it may be
  masked or left out, and the rest of the response is unchanged. Hiding must not
  produce a server error.
- **Preservation.** Everything that is not a credential keeps working exactly as it
  does today: ordinary configuration values, numbers and booleans keep their values
  and their JSON types, addresses without embedded credentials stay intact, and every
  response that works today keeps working. Do not hide a value merely because part of
  its name resembles a credential word.
- **Magnitudes.** A legitimate value is an ordinary setting such as a display field
  name, a number, or an address without credentials; the attack reads operator
  secrets such as a login name or a password.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
