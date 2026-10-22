# Table storage is not scoped to the caller

SeaweedFS's S3 gateway serves table storage through the S3 Tables API (table buckets, namespaces, tables, bucket policies, tags) and through an Iceberg REST catalog over the same data. Operators also manage table buckets with `weed shell` (`s3tables.*` commands), the admin console and `weed mini`.

**Observed impact.** On a gateway with an identities file, a user in their own account holding only ordinary S3 permissions sends a signed `ListTableBuckets` request and gets back other accounts' table buckets. That user can also read, change and delete what is in them.

## Security properties

- A caller may act on a table bucket, or on its namespaces, tables, policy or tags, only if the caller owns it, is an administrator, holds a permission for that operation, or the bucket's policy allows it. This applies to every operation and every front end that serves remote callers.
- Only an identity granted administrative permissions is an administrator; no other attribute of an identity makes it one.
- The open-by-default fallback (access when no policy decides) is only for requests with no credentials: servers with no identities configured, and requests served by a configured anonymous identity. An authenticated caller never gets access just because nothing denied it.
- Only authentication decides who a request acts as. A request without valid credentials never acts as an owner or an administrator, whatever else it carries, so a bucket policy's explicit Deny always applies to it.

## Contracts

- S3 Tables API: a refused operation returns a client error (4xx) and changes nothing. Iceberg catalog: a refused request returns an error response, reveals nothing and changes nothing. Listings leave out buckets the caller may not see.
- The catalog server may be embedded with its own authenticator. The properties hold for whatever caller that authenticator reports.
- These keep working exactly as today:
  - owners;
  - identities with administrative or wildcard permissions;
  - explicit table permissions and bucket policies;
  - requests with no credentials;
  - `weed shell`, the admin console and `weed mini`. These are trusted local tools that act for any account they name.

The scenario above is an example, not the full set of affected inputs.

## Constraints

- Fix the problem and its close variants; keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
