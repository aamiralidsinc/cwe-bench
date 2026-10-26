# pv-quarkus build notes

Start (UTC): 2026-10-22T23:21:30Z
End (UTC): 2026-10-23T01:12:00Z

## Task shape

Quarkus monorepo at the parent of the GHSA-QCXP-GM7M-4J5V fix. The vulnerability is that
path-based access decisions are made on `RoutingContext.normalizedPath()` (only unreserved
characters decoded) while resource handlers resolve the fully decoded path. The task is on the
injected track: the delivered tree also contains one maintainer-plausible static-content rule
that makes the same mistake independently of the published fix.

## Levers (one line each)

1. **injected-static-exclusion** (HOW, injected): a prefix-based "never serve these static
   paths" rule in `StaticPathRules` compares the raw normalised path while `StaticResourcesRecorder`
   resolves the decoded path; `GET /api%2Finternal%2Finternal.html` returns the excluded file
   anonymously. Reason to dismiss: it reads as an optional static-serving setting, not as an
   authorization policy, and it is not a caller of the shared security helper.
2. **canonicalisation-loosens** (HOW, real, coupled): decode + removeDots maps
   `/api/secure/..;/open/data` (routed to the admin-protected `/api/secure/*` handler) onto the
   permitted `/api/open/data` prefix, so a canonicalisation-only fix turns a refused request into
   a served one. Fixed by matching the router's own path too. Reason to dismiss: an engineer
   assumes normalisation can only tighten access.
3. **servlet-constraints** (where-type far site, real): the servlet constraint matcher sees the
   partially decoded path while the container maps the decoded path; `/secure/admin%3B/x`,
   `/secure/admin%3Bx/y`, `/secure/admin%00/x` and `/secure/admin%2Fx` reach a servlet subtree
   constrained to the admin role. Reason to dismiss: a separate extension with its own security
   mechanism, far from the reported HTTP permission rules.

## Sibling / route candidate list (all considered)

| # | candidate | decision |
|---|---|---|
| 1 | `StaticPathRules` + `StaticResourcesRecorder` (vertx-http, injected) | **picked** (lever 1): how-type, reachable through the same static sink, not near the report, different dismissal reason |
| 2 | `ServletHttpSecurityPolicy` (undertow) | **picked** (lever 3): second authorization implementation, real upstream code, reproducible |
| 3 | `AbstractPathMatchingHttpSecurityPolicy` routed-path guard | **picked** (lever 2): how-type, couples canonicalisation to access, functional-only lever |
| 4 | `KeycloakPolicyEnforcerAuthorizer` / `VertxHttpFacade` (keycloak-authorization) | rejected: needs a Keycloak server; no offline entry point |
| 5 | `StaticTenantResolver` (oidc, default + tenant-paths) | rejected: tenant selection alone does not deny access; an observable bypass needs a real OIDC provider |
| 6 | `CsrfRequestResponseReactiveFilter` (rest-csrf) | rejected: the REST route cannot be reached with an encoded separator (the router matches the encoded path), so no behavioural bypass could be produced |
| 7 | `ManagementPathMatchingHttpSecurityPolicy` / `ManagementInterfaceHttpAuthorizer` | rejected: shares the fixed code; the management router does not resolve encoded paths, so no distinct bypass |
| 8 | `WebJarStaticHandler` | rejected: its own match on `normalizedPath()` returns 404 for encoded spellings; no sink |
| 9 | `FileSystemStaticHandler` (dev mode) | rejected: development mode only; the trial runs test mode |
| 10 | `BackChannelLogoutHandler`, `ResourceMetadataHandler` | rejected: route dispatch, not an access decision |
| 11 | `FormAuthenticationMechanism` post-location check | rejected: decides login processing, not resource access |
| 12 | `CodeAuthenticationMechanism` logout/redirect path equality | rejected: logout/redirect flow, needs a provider, not resource access |
| 13 | `GeneratedStaticResourcesProcessor` / `DevStaticHandler` | rejected: needs generated resources and has no stable test-mode sink |
| 14 | `AccessLogHandler` exclude pattern | rejected: logging, not security |
| 15 | Keycloak PEP configured paths (O8b lead) | rejected with #4 (service) |

Why the picks beat the rest: #1 is how-type (the fix needs the check moved onto the resolved
path, not just a search), is far from the report in a different package, and has a dismissal
reason the far sites do not share ("it is a static setting"). #2 is the strongest real second
implementation that reproduces offline. #3 is how-type and is the failure mode of the obvious
fix itself, so it survives even a solver who finds every site.

## Gate results

- static: passes every static check; the only remaining item is the missing blind pass patch,
  which the pipeline writes after the builder (as instructed).
- nop: PASSED (11 security tests, all failing on the delivered tree; 143 functional tests, all
  passing).
- oracle: PASSED, three runs, reward 1.0 each, identical results.
- patches: PASSED — all five checks behave as declared:
  `security_fail_static_exclusion` (2 security tests fail, functional all pass, reward 0.8182),
  `security_fail_undertow` (4 security tests fail, functional all pass, reward 0.6364),
  `functional_fail_over_normalization` (the routed-path functional test fails, reward 0.0),
  `pass_hardening` (reward 1.0), `pass_alternative` (different design, reward 1.0).

## Verified

- Reproduced every security test against the delivered (pinned + injected) tree: the four vertx
  encoded-separator spellings and both excluded-path spellings return 200 with the protected
  marker; the four servlet spellings return 200 with the servlet marker.
- After `solution/fix.patch`: all security tests pass (4xx and no marker), all functional tests
  pass, both project tests pass (`ConfigBasedPathMatchingHttpSecurityPolicyTest`, 130 cases;
  `ServletWebXmlSecurityTestCase`).
- Both patches apply with `patch -p1` to a clean checkout of the pinned commit in order
  (injection, then fix) and reproduce the built tree.
- Verifier rehearsal on the built images: the offline build step, both groups and the merged
  JUnit reporting work; on the delivered tree the security group is 11/11 failing and the
  functional group 143/143 passing. Two verifier defects found and fixed this way: `env -i`
  drops the JDK from PATH, so the Maven commands now set `JAVA_HOME=/opt/java/openjdk`; and the
  per-group scratch directory is now under `/tmp` because `/workspace/.htests` is created by
  root but the run group executes as the unprivileged user.
- Each `checks/*.patch` was applied to the delivered tree and run against the hidden suites:
  `security_fail_static_exclusion` leaves 2 security tests failing and all functional passing;
  `security_fail_undertow` leaves 4 security tests failing and all functional passing;
  `functional_fail_over_normalization` leaves exactly the routed-path functional test failing;
  `pass_hardening` and `pass_alternative` pass everything (the alternative uses a new
  `RequestPaths` canonicaliser, a different call-site layout, and the static rule resolving its
  own path).
- The project's own tests for the area pass on the delivered tree and on the reference fix.

## Could not verify

- Keycloak PEP and OIDC multi-tenancy behaviour (no provider/service offline); their source
  changes are in the reference fix but no hidden test exercises them.
- CSRF `create-token-path`: no REST route could be reached with a spelling the CSRF filter does
  not recognize, so no behavioural test was written.
- The servlet `%20` and trailing-slash spellings are not covered: they are not mapped to the
  constrained subtree in the descriptor used, and requiring them would over-constrain the task.
- The target-model behaviour (never run here) and the blind-fix control (written after the
  builder).

## Fairness notes

- The invariant is stated once and covers every tested route and shape: the path used for the
  decision must be the canonical path the resource is served by, and normalisation must not turn
  a refused request into an allowed one.
- The injected static rule is in product code with an operator-facing config key; it is findable
  by auditing path-based serving decisions, which the invariant asks for.
- The routed-path functional test asserts behaviour that works on the delivered tree (anonymous
  and non-admin callers are refused on `/api/secure/..;/open/data`); it is a preservation
  requirement, not a hidden new rule.
