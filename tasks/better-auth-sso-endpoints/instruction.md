# Signing in through an SSO provider can make the server contact internal hosts

## The system

The application in `/app` is an authentication library. One of its features lets
an organisation offer single sign-on through an external OIDC identity provider.
A member with SSO-management rights can register such a provider and configure
the addresses the server uses to talk to it. When someone signs in through that
provider, the server contacts the provider and uses what it returns in the
sign-in.

The operator decides which origins are legitimate for their deployment through
the application's `trustedOrigins` configuration. Organisations that run their
identity provider on a private network are expected to add its origin there.

## What we observed

During a sign-in through a provider configured by a member with SSO-management
rights, our server sent requests to a service bound to loopback on the server's
own machine and used the responses in the sign-in. In another case it sent them
to the cloud instance-metadata address. Neither host is one we ever allowed an
identity provider to use.

## Required behaviour

- No provider configuration that a caller entitled to manage SSO can supply
  through the public API may cause the server to send a request to a host the deployment does not permit. A host is permitted only if
  it is publicly routable, or if its origin is listed in `trustedOrigins`. Any
  other host must never be contacted on a provider's behalf: for example a
  loopback, private-network, link-local or cloud instance-metadata address,
  however the address is written.
- Legitimate SSO must keep working exactly as today: a provider whose addresses
  are on origins listed in `trustedOrigins` (including an internal identity
  provider the operator put there) keeps working end to end, over HTTP or
  HTTPS. A provider whose addresses are on a publicly routable host is
  accepted.

## Constraints

- Fix the flaw in the library itself, for every way it can be reached, not
  only the example above. Do not special-case the example's hosts or values.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app` (a `pnpm` workspace). There is no network access.
Dependencies are installed and sibling libraries are pre-built, so source
changes take effect without a build step.
