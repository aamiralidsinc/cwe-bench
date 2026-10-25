# Unauthorized access to path-protected resources

The application is a Quarkus service that publishes both HTTP endpoints and static content
(pages, scripts, downloads) from its classpath resources. Operators restrict parts of the site
with path-based rules: a rule names a path prefix and the role, or the authenticated user,
required to reach anything beneath it.

We found that restrictions of this kind can be walked around. With a rule requiring the `admin`
role for everything under a protected prefix, an anonymous caller can fetch a protected page by
writing the request path with a percent-encoded path separator:

```
GET /api%2Fadmin%2Fadmin.html   -> 200, protected page body
GET /api/admin/admin.html       -> 401
```

The same request is refused when it is written in the ordinary way and served when the separator
is encoded.

**Required invariant.** For every request, the path used to decide whether a protection applies
must be the same canonical path by which the resource is identified and served. No spelling of a
request path may cause a request that would be refused for that path to be served instead, and no
normalisation may turn a request that is refused today into one that is allowed: whatever resource
a request actually reaches must still be covered by the decision that covers its canonical
location. This holds for every protection the product applies based on a request path, and for
every mechanism that serves the resource.

**Contracts.**

- A refused request is answered with a client error (a 4xx response) and the protected content is
  not returned.
- Path parameters written in the ordinary way stay ignored for the access decision.
- Everything that works today keeps working: callers with the right role reach the resources their
  rules allow, and public resources stay reachable to anonymous callers, including when a public
  path is written with an encoded separator.

The example above is one way to reach the problem; it is not the full set of affected paths,
spellings or rules.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
change for this report, and do not special-case the example.
