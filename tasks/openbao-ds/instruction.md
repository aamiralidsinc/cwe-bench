# OpenBao — identity values widening authorization matches

## What this is

OpenBao is a secrets-management server. Clients authenticate and receive a token
whose access-control policies name the paths that token may use. The same identity
placeholders that fill policy paths also fill the allow-lists on certificate-issuing
roles, so one written rule or role can adapt to who is calling.

Placeholders take the form `{{identity.entity.metadata.<key>}}` (and the related
entity, alias and group forms) and are replaced at use time with the caller's
identity data.

## Observed problem

A user who can set a metadata key on their own identity entity can read a secret
outside the paths their policy names. Setting that key to a path wildcard and then
requesting a path the written rule was never meant to cover returns the secret.

## Security properties (invariants)

- No value substituted from identity data may introduce a pattern metacharacter into
  an authorization pattern. This holds wherever a substituted value is matched
  against something the caller supplies — a request path, or a name, identifier or
  host in a certificate request — and for every identity source (entity, alias and
  group names and metadata).
- Pattern metacharacters here include the wildcards used when a path pattern is
  matched, the star used when a name, identifier or host pattern is matched, the
  separator that splits an allow-list into entries, and the path separator.
- A request that would rely on such a value is refused with a client error and no
  side effect: no secret is returned and no certificate is issued or signed.
- Metacharacters written literally into a policy or role by an administrator keep
  their present meaning. Only substituted values are subject to this rule.
- Legitimate substitutions keep working exactly as today: a caller whose identity
  data is an ordinary allowed value still reads the paths that value grants and
  still receives certificates for it.

## Keep working

- A policy path that places a placeholder next to a literal wildcard, such as a
  trailing `*`, continues to match as it does now.
- A certificate-role allow-list that is a literal glob written by an administrator
  continues to match exactly as it does now.
- An allow-list entry that is a single literal star still means "any".
- A default user or similar principal filled from identity data is still used when a
  role names one, and its rendered value is still re-checked against the allow-list
  afterwards.

The examples above are examples, not the full set of cases.

## Constraints

- Fix the underlying problem and its close variants, not just the one example
  trigger shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example values.
- Do not look up the upstream fix for this issue.
