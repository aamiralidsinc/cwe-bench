# FAIRNESS — pv-quarkus

Paths below are relative to `tasks/pv-quarkus/tests/`. The harness drives real HTTP through the
real router/static/servlet entry points; nothing bypasses a valid layer.

## 1. Test-by-test

| test (file::name) | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| security/vertx-http/HiddenStaticPathAuthzTest.java::protectedStaticContentIsNotServedToAnonymousCaller (5 cases: `%2F`/`%2f` in first/middle position) | any 4xx and neither ADMIN nor SECRET marker | "No spelling of a request path may cause a request that would be refused for that path to be served instead"; contract "a client error (a 4xx response)" | no — canonicalising the decision path and deferring to the existing policies gives 401/403; any 4xx accepted | low |
| security/vertx-http/HiddenStaticExcludedPathTest.java::excludedStaticContentIsNotServed (2 cases) | any 4xx, no INTERNAL marker | "This holds for every protection the product applies based on a request path, and for every mechanism that serves the resource"; "whatever resource a request actually reaches must still be covered by the decision that covers its canonical location" | no — exclusion checked on the resolved path falls through to 404 | low |
| security/undertow/HiddenServletPathAuthzTest.java::constrainedServletIsNotServedToAnonymousCaller (4 cases: `%3B`, `%3Bx`, `%00`, `%2F`) | any 4xx, no SERVLET marker | intro ("a rule names a path prefix and the role ... required") + "every protection ... based on a request path ... every mechanism that serves the resource" | no — canonicalising in the servlet policy gives 401 | low |
| functional/vertx-http/HiddenStaticPathAuthzFunctionalTest.java::administratorReadsProtectedStaticContent | 200 + ADMIN body | "callers with the right role reach the resources their rules allow" | no | low |
| ...::authenticatedUserReadsSecretStaticContent | 200 + SECRET body | same | no | low |
| ...::publicStaticContentStaysPublic | 200 + PUBLIC body | "public resources stay reachable to anonymous callers" | no | low |
| ...::publicStaticContentStaysPublicWhenWrittenWithEncodedSeparator | 200 + PUBLIC body for `/api%2Fpublic%2Fpub.html` | "including when a public path is written with an encoded separator" | no (a blanket reject-all-encodings fix is excluded by this same sentence) | low |
| ...::pathParametersStayIgnoredForTheAccessDecision | 401 anonymous, 403 user for `;a=1` | "Path parameters written in the ordinary way stay ignored for the access decision"; "Everything that works today keeps working" | no — these are today's auth outcomes, preserved when the fix defers to the policy | low |
| ...::excludedStaticContentIsNotServed | 404 and no INTERNAL marker for the ordinary spelling | "Everything that works today keeps working" (today's excluded-path outcome is 404); contract 4xx | no — excluded-paths is a fall-through to the next handler, so a correct fix keeps 404; turning it into an explicit 403 would change the setting's meaning. Exact 404 is narrower than the 4xx contract (Quality) | low |
| ...::otherStaticContentIsStillServed | 200 + PUBLIC for nested path | public stays reachable | no | low |
| ...::protectedRouteIsNotLoosenedByPathCanonicalisation | 401 anonymous, 403 user, no ROUTE marker for `/api/secure/..;/open/data` | "no normalisation may turn a request that is refused today into one that is allowed: whatever resource a request actually reaches must still be covered by the decision that covers its canonical location" | no — the stated primary mechanism checks the routed path too; canonical-only matching violates this sentence | low |
| ...::administratorStillReachesProtectedRoute | 200 + ROUTE body | right role reaches its resources | no | low |
| functional/undertow/HiddenServletPathAuthzFunctionalTest.java::administratorReachesConstrainedServlet | 200 + SERVLET body | right role reaches its resources | no | low |
| ...::anonymousCallerIsRefusedOnConstrainedServlet | 401 | contract 4xx (401 is the servlet-standard and today's outcome) | no | low |
| ...::unconstrainedServletSubtreeStaysAccessible | 200 + SERVLET body | "Everything that works today keeps working"; public stays reachable | no | low |
| project test `ConfigBasedPathMatchingHttpSecurityPolicyTest` (130 cases) | existing project expectations | visible repo regression; "Everything that works today keeps working" | no (reference passes it) | low |
| project test `ServletWebXmlSecurityTestCase` | existing project expectations | same | no (reference passes it) | low |

## Verdict reasoning

READY. Reference and `pass_alternative` both score 1.0. Security tests accept any 4xx; the
functional exact statuses (401/403/404) are today's outcomes, reproduced by any fix that defers to
the existing decision points. The one route the instruction does not name, the injected
excluded-paths rule, is covered by the general property read literally: it is a path-based
decision applied by the mechanism that serves the resource. A fix following the primary mechanism
— canonical decision path, plus the routed path so canonicalisation cannot loosen — passes
everything, so gate a does not fire.

## Required: generalize

1. "publishes both HTTP endpoints and static content (pages, scripts, downloads) from its
   classpath resources" → "publishes resources over HTTP." (names the serving stages/format where
   the injected sibling lives)
2. "Path parameters written in the ordinary way stay ignored for the access decision." → "The
   access decision does not change with segments that do not change the resource a request
   reaches."
3. "public resources stay reachable to anonymous callers, including when a public path is written
   with an encoded separator" → "public resources stay reachable to anonymous callers, whatever
   spelling reaches them."

## Quality to tighten

- Leniency. Traps: missing static rule → `HiddenStaticExcludedPathTest`
  (`security_fail_static_exclusion`); canonical-only matching → `protectedRouteIsNotLoosened...`
  (`functional_fail_over_normalization`); vertx-only → `HiddenServletPathAuthzTest`
  (`security_fail_undertow`). Reject-all-encodings is caught by the public-encoded 200 test;
  crash/500 or 4xx-with-body by `clientError` plus marker checks; refuse-all by the four 200
  tests and the project tests. Not caught: request-side-only canonicalisation (no configured rule
  path is encoded), block-anonymous-only encoded cases, and the untested OIDC / Keycloak / CSRF /
  hot-deployment sites (a partial fix scores 1.0).
- Hints: generalize the three sentences above; delete "The example above is one way to reach the
  problem; it is not the full set of affected paths, spellings or rules" and the "no normalisation
  may turn a request that is refused today into one that is allowed" clause (the preceding
  outcome sentence covers it).
- Status: `excludedStaticContentIsNotServed` demands 404 where the contract promises any 4xx;
  `clientError()` plus marker absence would match it.
- Realism: all three traps are maintainer-plausible product code reachable through the real entry
  points; nothing planted or contrived.

Human review: confirm the exact 404 on the ordinary excluded path is intended as preservation of
the excluded-paths fall-through, and that the injected excluded-paths rule is meant to be covered
by "every protection ... based on a request path".

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
