# fastify-s2 - build notes

- Start: 2026-10-25T22:55Z
- End: 2026-10-25T23:20Z
- Repo: fastify/fastify, pinned 179619c8 (5.12.1), published fix 7de6e816.
- Pattern A+B, track injected.

## One-line levers

- **T1 base (A, report site)**: the four request-part branches in `lib/validation.js` (headers:236,
  body:255, querystring:273, params:279) and the compiler-setup gate `lib/route.js:425` select a
  schema by truthiness, so a JSON Schema boolean `false` is read as "no schema" and no validator is
  compiled; the security tests cover body/headers/querystring/params, the extended route API and a
  multi-method route.
- **T2 alias (A, far site)**: `lib/schemas.js:67` materialises the documented `query` alias into
  `querystring` only when it is truthy, so `schema: { query: false }` never reaches the compiler;
  one file away from the landing point, in a module that looks like plumbing.
- **T3 fallback (B, protection never existed)**: `lib/four-oh-four.js:148` stores the not-found
  handler's `schema` in its Context but nothing normalises or compiles it, so every schema declared
  there - boolean or object - is ignored. Fixing it also needs `attachValidation: false` on that
  Context (`lib/four-oh-four.js:157`), otherwise a validation error is attached and the handler
  still runs. Published fix never touches the file.
- **T4 coupled (how)**: presence by key (`Object.hasOwn`/`in`) compiles an explicitly `undefined`
  part and breaks the documented FSTWRN001 warning-and-start behaviour; `null` must fail closed at
  ready; `true` must admit; a per-route custom compiler must receive the literal boolean;
  `attachValidation` must keep working. Caught functionally (overbroad.patch).
- **S1 defaults (injected, merged/default route)**: `lib/schema-defaults.js:28` merges server-wide
  default request schemas into routes; `defaultSchema[part]` truthiness drops a `false` default.
  Public `fastify.setDefaultSchema`, applied in `lib/route.js` `route()`; published fix never
  touches the module or method.
- **S2 inline (injected, second implementation)**: `lib/request.js:346` `request.validateSchema`
  returns true early for any falsy schema, so a request-time `false` schema is skipped. Sits next to
  the existing `compileValidationSchema` / `getValidationFunction` / `validateInput` APIs; published
  fix never touches request.js.

Every lever sits under the one general property: any schema the application has supplied for a
request must be enforced before its handler runs, and a schema that matches nothing must refuse
every such request with a client error and no handler side effect - whatever the schema's value
kind, whichever part of the request it describes, wherever in the application it was supplied.

## What was verified

- Pinned (injected) tree, behavioural probes: `body/headers/querystring/params: false` all return
  200 with the handler running; `query: false` bypasses silently (no warning); `body: null`
  bypasses with FSTWRN001; `setNotFoundHandler({schema})` ignores false and object schemas alike;
  `setDefaultSchema({body:false})` drops the default; `request.validateSchema(false, data)` returns
  true. Content-map `false` throws FST_ERR_SCH_CONTENT_MISSING_SCHEMA at ready (fail-closed, not a
  tested bypass).
- Oracle (= published fix + fallback wiring + defaults merge + inline helper) returns 4xx and never
  runs the handler for all 14 security tests; all 12 functional tests pass; the project subset
  (244 cases across test/schema-feature.test.js, test/route.7.test.js,
  test/validation-error-handling.test.js, test/internals/validation.test.js,
  test/internals/request-validate.test.js, test/404s.test.js) passes on the injected tree and on
  the oracle.
- Every checks/ patch was applied to the injected tree and both hidden suites run locally:
  miss_base 11 security fail / 0 functional; miss_alias 1 / 0; miss_fallback 2 / 0; miss_default
  1 / 0; miss_helper 1 / 0; verbsplit 8 / 0; crash 10 / 0; overbroad 0 / 1; refuse_all 0 / 9;
  hardening 0 / 0; alt_fix 0 / 0. Project subset also green for miss_base, hardening and alt_fix.
- `test/route-shorthand.test.js` fails 2 cases (QUERY method) on the *pristine pinned* commit under
  Node 20 on this host, before any of our changes; excluded from the project subset.

## Candidate sibling sites found, and why the picks won

Real (unmodified upstream), from the screener O8/O8b list plus my own search:
1. `lib/four-oh-four.js:148` - not-found handler schema never compiled. **chosen (T3)**: real,
   undocumented, a route family whose protection never existed, and the published fix never touches
   it; the attachValidation coupling makes it a how-type fix rather than a one-line wire-up.
2. `lib/schemas.js:67` - the `query` alias. **chosen (T2)**: the published fix does protect it, it
   is a second producer of the canonical part one file away, and its dismiss reason (normalization
   plumbing) is different from T3's.
3. `lib/validation.js` params/body/headers/querystring + `lib/route.js:425` - **chosen (T1)** as the
   report site, covering every entry point the published fix protects.
4. Explicit `undefined` / `null` / `true` / custom compiler / attachValidation - **chosen (T4)** as
   the coupled must-keep-working value that defeats `Object.hasOwn` fixes.
5. `lib/schemas.js:83` content-type maps (`body.content[t].schema === false`) - rejected: the pinned
   tree throws FST_ERR_SCH_CONTENT_MISSING_SCHEMA at ready, so it fails closed; no request bypass
   and fixing it would invent a feature the advisory does not describe.
6. `lib/schemas.js:105` response content schemas - rejected: serialization, a different protection.
7. `lib/route.js:617` `validateSchemaBodyOption` - rejected: registration guard, fail closed.
8. `lib/validation.js:19` response serializer setup - rejected: response side.
9. `request.validateInput(data, false)` - rejected: the existing API deliberately refuses non-object
   schemas with FST_ERR_REQ_INVALID_VALIDATION_INVOCATION (fail closed); turning it into a denial
   would be a behaviour change, not the advisory's protection.

Injected siblings considered:
- **S1** server-wide default request schemas (new `lib/schema-defaults.js`, `fastify.setDefaultSchema`,
  merge in `route()`): chosen. Realistic (header schemas are commonly repeated), reachable through
  `fastify.route`/shorthands, and its merge decision is a separate presence check the published fix
  never touches. Dismiss reason: defaults look like a convenience wrapper around the route's schema.
- **S2** request-time inline validation helper (`request.validateSchema`): chosen. It is the second
  implementation of the same guarded operation, next to an existing family of request validation
  APIs, and it is documented in the injected copy. Dismiss reason: an application's own imperative
  call reads as user code, not route configuration.
- S3 validator-compilation cache keyed by schema identity - rejected: a poor cache would also break
  the report's own repro, so the model would find it immediately; it is a visible cost, not a scope
  trap.
- S4 plugin-scoped default schema through `register()` options - rejected: same shape and same
  dismiss reason as S1, so it would add volume, not a second kind of lever.
- S5 auto-generated HEAD route stripping the GET schema - rejected: the security effect is a
  read-only HEAD request, and the "schema applies to a generated route" claim is arguable; not fair.

## Not verified / unknowns
- The hidden suites and every patch variant were first verified with the host's Node 20 against the
  pinned and oracle worktrees, then re-verified through the Docker gate (Node 22 images); the
  project subset was run the same way.
- `test/route-shorthand.test.js`'s two QUERY-method failures may disappear on the image's Node 22;
  it is not in the project subset either way.
- Whether the injected default-schema and inline-helper APIs are "what a maintainer would add" is a
  judgement call; both are documented and typed in the injected copy so a blind engineer can find
  them from the report's general property.
- Scoring keys on `classname::name` from Node's JUnit reporter, whose classname is always `test`;
  every hidden test name is therefore globally unique inside its group.

## Gate results (2026-10-25)

- `static`: PASSED (missing `blind.patch` and `FAIRNESS.md` only, as the process allows).
- `nop`: PASSED - 14 security tests fail on the pinned+injected tree, 219 functional tests pass.
- `oracle` (strict, 3 runs): PASSED - every run reward 1.0 and identical results.
- `patches`: PASSED - all 11 checked variants behaved as declared:
  - security_fail: miss_base (11 failing), miss_alias (1), miss_fallback (2), miss_default (1),
    miss_helper (1), verbsplit (8), crash (10), each with 0 functional failures;
  - functional_fail: overbroad (6 functional failures), refuse_all (61 functional failures);
  - pass: hardening 1.0, alt_fix 1.0.
