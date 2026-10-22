# Remote callers and web pages can read and change a running mock server's state without a credential

## System

This project runs local mock APIs from an operator-defined environment. The
runtime serves the operator's own mock traffic, and it also makes runtime state
and a record of the traffic it has served available to remote callers so that
the operator's tools and scripts can inspect and adjust them.

## Observed impact

Anyone who can reach the runtime's port can read and change that state and the
recorded traffic with no credential at all, and so can any web page the operator
happens to open. A page served from an unrelated origin can read credentials the
operator sent to the mock during normal use, and the same callers can make
changes that affect how the runtime will behave.

## Security property that must hold

State and recorded traffic that the runtime makes available to remote callers,
and every update of it, are accessible only to a caller presenting the secret
the operator configured. This holds for every exposure, every operation and
every way the runtime is run or embedded. When no secret is configured, the
runtime generates one and reports it to the operator, and remains closed to
everyone else. An absent, malformed or wrong secret is refused.

No record of served traffic that the runtime produces, in any form or for any
consumer, may contain the value of a sensitive request or response header.
Header names and every non-sensitive value remain available.

No cross-origin grant may be given to a web origin the operator did not list,
on an ordinary response or a preflight; refusing the preflight is an acceptable
outcome. Including `*` in the configured list is the operator's explicit opt-in
to a wildcard.

A caller may change process-environment values only under the operator's
configured prefix. A key supplied without that prefix must never reach the
process environment under its bare name, and no such change may take effect
when the configured prefix is empty.

## Contracts the fix must honor

- The secret and the allowed origins are supplied through the runtime's public
  configuration: the `adminApiAuthToken` option or the `MOCKOON_ADMIN_API_TOKEN`
  environment setting for the secret, and the `adminApiCorsOrigins` option (an
  array of origins) for the allowed origins. Callers present the secret as
  `Authorization: Bearer <secret>`. A client that cannot set request headers
  presents the same secret as a `token` query parameter; that form is never a
  substitute for the header on a request that can carry one.
- A refused request is answered with a client error and has no side effect; a
  refused continuing exposure may simply deliver nothing. An allowed origin is
  echoed back, or `*` is returned when the operator opted into the wildcard.
- Ordinary user-defined mock traffic, together with the headers and cross-origin
  behaviour the environment configures for it, keeps working without the secret.
  Existing reads of process-environment values keep their automatic prefix, and
  writes under the configured prefix keep working.
- Sensitive headers are `authorization`, `proxy-authorization`, `cookie`,
  `set-cookie`, `api-key`, `x-api-key` and `x-auth-token`. A configured secret is
  an ordinary value of a few dozen characters.

The values and examples above are illustrative, not the full set of cases the
rules cover.

## Constraints

- Fix the problem and its close variants, not just the examples above.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example origin, secret or header.
