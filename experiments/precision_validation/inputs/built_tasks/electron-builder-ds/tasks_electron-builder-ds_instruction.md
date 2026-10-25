# Credentials and secrets must not leave the origin or the diagnostic boundary they belong to

This project is a set of tools for desktop applications. Those tools make network requests, some
of which carry a credential the operator supplied, and they are given secrets for the services
they use.

## Observed impact

A credential supplied for one origin reached a different origin after a server redirected a
request, and a configured secret was written in clear text into diagnostic output.

## Security property

A credential is bound to the origin — the scheme, host and port — it was supplied for. No request
the product makes may carry it to any other origin, at any hop and by any path, however that
credential is expressed: as a request header (standard or application-specific, in any spelling or
case), as connection-level authentication, or otherwise. After a redirect to another origin the
request may continue only without the credential.

A secret the product is given must not appear in clear text in any diagnostic output the product
emits, whether an error message or debug output, and whatever name the field, option, argument or
variable holding it has.

## Contracts the fix must honor

- A cross-origin redirect must not carry the credential onward. The request may continue at the new
  origin without it, and the operation it belongs to must still complete by its normal path or by
  an equivalent fallback; a clean internal failure is acceptable only where the overall operation
  still completes. A refusal or failure must not leave the credential with the other origin, must
  not crash, and must not break a later legitimate operation.
- Redirects keep working. A request redirected within the same origin keeps its credentials and
  completes, and so does an upgrade from unencrypted to encrypted transport on the same host with
  standard ports. After a redirect to another origin the request still completes there, and
  ordinary non-credential headers still travel with it. Private servers keep working.
- Every legitimate operation keeps working exactly as it does today, and no capability or result
  the product already provides is removed. Diagnostic output still contains everything that is not
  a secret, and a sanitized error still identifies which setting or variable is wrong.

## Constraints

- Fix the underlying behaviour; do not special-case any example.
- Keep legitimate use working as described.
- Do not modify or add tests.
- Do not look up the upstream fix.
