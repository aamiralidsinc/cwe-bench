# A host value is recorded without being a single host

## System

guzzlehttp/psr7 is the PSR-7 URI and message library used by Guzzle and by many
PHP HTTP clients, proxies and server adapters. It represents URIs, requests and
HTTP messages, and derives the `Host` header and the serialized authority from
the URI's host component.

## Observed impact

A value that is not a single host is accepted and recorded as the host, so the
host the library reports and the host a consumer sees in the serialized
authority or `Host` header disagree. For example:

```php
$uri = (new Uri())->withHost('partner.example@evil.example');
$request = new Request('GET', $uri);

$request->getUri()->getHost();      // "partner.example@evil.example"
$request->getHeaderLine('Host');    // "partner.example@evil.example"
```

In the serialized authority `//partner.example@evil.example`, `partner.example`
is user information and `evil.example` is the host. A component that trusts the
reported host and a component that follows the request address can therefore
treat different origins as the same origin.

## Security property that must hold

Any host value that the library accepts, records, or uses to derive a `Host`
header or a serialized authority must be a single well-formed authority host,
however the value arrives and whichever object supplies it. A well-formed
authority host:

- contains no control character, space, `/`, `?`, `#`, `@` or `\` character;
- contains no `:` unless the value begins with `[` and ends with `]` (a port
  belongs in its own component, never in the host);
- contains no `[` or `]` unless the value begins with `[` and ends with `]`.

A value that is not a single well-formed host must be refused instead of being
recorded, and any host the library does record must agree with the authority
that is serialized from it.

## Contracts the fix must honor

- **Refusal form.** Refusing raises `InvalidArgumentException` (or a subclass),
  and nothing is recorded or emitted for the refused value.
- **Preservation.** Everything that is legitimate keeps working exactly as it
  does today. A host that begins with `[` and ends with `]` keeps being accepted
  even when its contents are not a valid IP address; an internationalized name
  keeps working; a port supplied as its own component keeps working; an empty
  host keeps working; and a complete authority (user information and/or a port
  together with a host) is still split into its components, with only the host
  component subject to the rule above.
- **Magnitudes.** Legitimate values are ordinary hosts such as `example.com`,
  `[::1]`, a host with port `8080` supplied separately, and an internationalized
  name. The attack is a value that folds user information, a path, a query, a
  fragment, a backslash, a port, or a bracket fragment into the host.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
