# orval-ds build notes

start_utc: 2026-10-18T20:11Z
end_utc: (open)

Repo: orval-labs/orval. Pinned = parent of 8ef1bfdf3f9bcaf9dabfbe2e42887f1c0e159ab6
= c082bb4aff4f9aaee196a1ca948492f0e28d6e79 (verified locally). Fix commit cherry-pickable from clone.

## Task shape
orval is a TypeScript code generator: it reads an OpenAPI/Swagger document and writes TypeScript
clients, validation schemas, mocks and server scaffolding. Spec-controlled strings (schema
defaults, property/parameter names, server URLs and variable defaults, media-type keys, form field
names, route text) are embedded into generated program text. Unescaped, a malicious document turns
into live code in the generated module. `instruction.md` states the invariant ("no spec value may
change the structure of generated source or execute") and the coupled preservation rules.

## Levers (each one line; file:line at pinned)

Pattern A - sites the published fix covers (report lands on zod defaults):
A1 zod default value emitted as a module const after `stringify(...)` swaps ' for ` (zod/src/index.ts:842-846);
   backtick / ${ in a default becomes live. Shapes: plain string (backtick and ${), array-of-string, enum default.
   Dismiss reason: none; this is the reported site. Blind fix must generalise past one literal.
A2 zod object/property keys emitted as `"${key}"` (zod/src/index.ts:1519-1521, 1870, 2054-2056, 817-836).
   Dismiss reason: double-quoted keys look safe; only a `"` in a key breaks out (computed key).
A3 shared getKey wraps non-identifier keys in single quotes without escaping (core/getters/keys.ts:4),
   reaching model types, query params and MSW mock object values. Dismiss reason: it is @orval/core and
   the output looks like mock/test scaffolding.
A4 core route getters: getRoute static text into backtick URL literals (core/getters/route.ts:34-66),
   getFullRoute servers[].url and server variable defaults (route.ts:94-115). Dismiss reason: paths are
   "URLs, not code"; the defaults route needs baseUrl.getBaseUrlFromSpecification.
A5 query package: getRouteAsArray static segments in single quotes (route.ts:161-179) and the mutation
   invalidation prefix passed raw to getFullRoute (query/mutation-generator.ts:353, 311-312).
   Dismiss reason: cache-key bookkeeping; and "the core helper is fixed, so callers are safe".

Pattern B - real, unmodified upstream routes the published fix never touches (confirmed open at pinned):
B1 effect output: string default quote-swapped to backticks (effect/src/index.ts:298-302).
   Dismiss: different output package, "the advisory says zod".
B2 hono's own route copy embedded in single-quoted route registration and Context type
   (hono/src/route.ts, hono/src/index.ts:170, 756). Dismiss: server generator, second implementation.
B3 MSW's own route copy embedded in a single-quoted handler URL (mock/src/faker/getters/route.ts,
   mock/src/msw/index.ts:470). Dismiss: mock/test scaffolding.
B4 media-type key emitted raw as a request Content-Type header (fetch/src/index.ts:463;
   core/generators/options.ts:621). Dismiss: "protocol metadata, not code".
B5 form-data field name emitted inside a backtick literal (core/getters/res-req-types.ts:769-876).
   Dismiss: body field names, not paths.
B6 factory-method date default emitted raw inside new Date('...') (core/generators/factory.ts:491).
   Dismiss: mock factory helper, "it is a date, not a string".

Injected siblings (our copy only; recurring trust decision; published fix never touches these):
I1 zod $ref-sibling default path uses the same ' -> ` quote swap as the main default path
   (zod/src/index.ts:450-456). Reachable with generateReusableSchemas. Same omission shape.
I2 effect object-default keys emitted bare (effect/src/index.ts:271-286) - the same omission zod had
   before its object-key fix; effect's own string-default path (B1) has the same trust decision.

## Tests by lever (real entry point: generate() from the built orval package; then the generated
module is loaded by a fresh bun process with stubs, and a caller-supplied marker shows execution)
S1 zdef_bt, zdef_interp, zdef_array, zdef_enum           -> A1
S2 zkey_classic, zkey_mini, zkey_allof, zkey_objdefault   -> A2
S3 mock_key (split mode, faker module)                    -> A3
S4 path_bt, srv_url, srv_var                              -> A4
S5 qarr (split query key), mutpref (invalidation prefix)  -> A5
S6 effect_def                                             -> B1
S7 hono_r, msw_r                                          -> B2, B3
S8 ctype, formdata                                        -> B4, B5
S9 factory_d                                              -> B6
S10 zrefsib                                               -> I1
S11 effect_objkey                                         -> I2

## Coupled must-keep-working (functional)
- {param} still becomes a runtime interpolation; `$` without `{` stays literal; backslashes round-trip.
- {env} server variables still substitute; normal server URL still prefixes requests.
- String/array/enum/non-string defaults evaluate to the exact same values (including backtick/${ data).
- Object keys with quotes/backticks stay data keys.
- Split query keys return the same array; invalidation predicate still matches the legit prefix.
- Hono route still registers ':param'; MSW route still matches '*/path/:param'.
- Content-Type header still present; form-data field name still appended.
- Factory date default still yields the specified date.
- Project's own core route/string unit tests (copy in tests/functional) pass.

## Verified so far (pinned tree)
- Every A/B/S site above reproduces injected execution through generate() at the pinned commit
  (probe scripts, marker observed), except I1/I2 which are the injected siblings (added here) and
  zrefsib which is safe at pinned until I1 is applied.
- All-probe outputs generated with the real orval CLI (dist built from pinned commit).
- Node/bun toolchain works: bun 1.3.14, `bun install --frozen-lockfile`, `bun run build`.

## Not verified yet
- The complete image build and offline behaviour (next).
- Gate stages.

## Update 2026-10-18T20:55Z — build and local verification
- Injection applied to our copy only (environment/injection.patch): I1 zod $ref-sibling default
  swap; I2 effect object-default bare keys.
- Oracle = fix.patch (source-only, no new packages): shared template-literal escape helper in core
  utils; escaping in core route getters (path, servers[].url and variable defaults, getRouteAsArray),
  getKey, form-data field names, factory date default, Content-Type literals, zod defaults/keys/ref
  sibling, effect defaults/keys, hono route helper, MSW route helper, mutation prefix + prefix
  literal. 12 files, no dependency changes.
- Local suite (same files the verifier runs), on the pinned+injection tree: 22/22 security tests
  fail, 19/19 functional tests pass, project route/string tests 95/95 pass.
  On the oracle tree: 41/41 hidden tests pass (19 functional + 22 security), project tests 95/95.
- Wrong-fix checks verified locally: pass-alt (unicode-escape alternative) 41/41;
  pass-hardening (oracle + line-terminator escaping + __proto__ quoted key) 41/41;
  ff-overbroad (query-array interpolation removed) 1 functional failure, security clean;
  sf-miss-effect-default leaves exactly the effect security test failing.
- Register: seven pattern-B/route rows appended to build/audit/uncovered-routes.tsv.
- Could not verify yet: Docker image build, Harbor trials, the strict gate stages.

## Gate progress (Harbor)
- static: FAILS only on the two deferred items (checks/blind.patch, build/<slug>/FAIRNESS.md);
  instruction leak scan clean otherwise.
- nop: PASSED (22 security tests, all fail on the untouched tree; 113 functional tests, all pass).
- oracle: PASSED 3/3 runs, reward 1.0 in every run, identical results.
- patches: running (18 checks; blind entry temporarily left out of manifest while it runs because the
  blind patch is written later by the fresh-agent pass).
- Image build verified locally; verifier also exercised directly in the image (nop reward 0.0,
  oracle reward 1.0).

## Shared-host note (patches stage)
The first patches-stage attempt failed in Harbor with "failed to set up container networking:
network ... not found" - gate.py prunes unused Docker networks before every trial, and ~20
concurrent gate runs on this host prune each other's freshly created trial networks. The same
error then left a compose start hanging. A local watcher now attaches a short-lived sleeper to this
task's own trial network as soon as compose creates it, so concurrent prunes no longer remove it.
This is host infrastructure only; nothing in the task depends on it. Representative checks were
also run directly in the built image (no compose networks) and behaved as declared.

## Patch-check evidence (2026-10-21:52Z)
All 18 manifest patch checks behave as declared. Sixteen were run directly in the built image
(same tests/, same test.sh, no compose network); the two zod checks were verified by the gate's
Harbor trials before the shared-host network race became frequent. Full table:
build/orval-ds/checks-verification.md.
- every sf-miss-* leaves only its own lever's security tests failing, functional clean;
- pass-alt (unicode-escape alternative) and pass-hardening reward 1.0;
- ff-overbroad (query-key interpolation removed) fails only functional tests.

## Final status 2026-10-18T21:56Z
end_utc: 2026-10-18T21:56Z (this session)

Gate stages:
- static: FAIL only on the two deliberately deferred items (checks/blind.patch, FAIRNESS.md);
  everything else clean (no instruction leaks, no hidden tests in environment/, offline allowlist,
  kill block present, catalogue complete).
- nop: PASSED - security 0/22 (all fail on the untouched tree), functional 113/113.
- oracle: PASSED - 3/3 runs reward 1.0, identical results.
- patches: NOT COMPLETED under Harbor on this host. The stage passed its first two checks
  (sf-miss-zod-defaults, sf-miss-zod-keys; each 4 security failures, 0 functional), then every
  later attempt died with "failed to set up container networking: network ... not found": ~20
  concurrent gate runs on the shared host each call `docker network prune -f`, deleting other
  trials' freshly created compose networks. A network-keep watcher reduced but did not remove the
  race. All 18 checks were instead run end-to-end in the same image with the same /tests and
  test.sh, and every one behaves as declared - see checks-verification.md. Two checks were verified
  by the gate's own trials and sixteen by the direct image runs; there is no check left unverified.
  The remaining formal step is a run of `gate.py orval-ds --only patches` on a host without the
  concurrent prune race (the full gate run that follows the blind/FAIRNESS pass will do it).

What was verified: entry point (real CLI, generated module loaded in a fresh runtime), every lever
reproduces at pinned and is inert under the oracle, legitimate behaviour preserved, project tests
95/95 on both trees, image offline after build.

What could not be verified: the formal patches-stage PASS on this host (infrastructure, above);
target-model trials (not run here by instruction).

Out-of-scope note: the advisory's fix bundles sibling advisories and some sites outside this
protection (e.g. a route string in a TypeScript type argument, where nothing executes); this task
covers only the generated-source escaping class within this repository at the pinned commit, and
every tested route is in that class.

## Hardening round 2026-10-22 (T16 + T17, Frontier 1.4 conversion)

Both target models had solved the 15-trap build, so two new fair levers were added; the delivery
format was converted to Frontier 1.4 (workdir /workspace, separate offline verifier, uid-1000
grading, artifacts restore, canary GUID).

- T16 operation identity metadata (uncovered route B, real upstream code):
  `packages/query/src/query-generator.ts:683,761` and
  `packages/query/src/mutation-generator.ts:610` interpolate `operationId` verbatim into the
  single-quoted third argument handed to a custom query/mutation options mutator. Reason to
  dismiss: it is tooling metadata for a user-supplied mutator, not request code, and operationId
  is an identifier whose generated names are sanitized. Three copies across two files, so a fix
  at the first copy still leaves the others.
- T17 composed-type required/discriminator names (uncovered route B, real upstream code):
  `packages/core/src/getters/combine.ts:160,195` interpolate the names into quoted type-level
  utility arguments (`Omit<..., '...'>`, `Required<Pick<..., '...'>>`). Reason to dismiss: the
  position is a TypeScript type, which is erased at runtime. A `'` closes the literal and the
  remainder is a valid top-level statement, so the generated module executes it on import; the
  functional pair keeps required/optional semantics intact.

Harness: `generateCase` accepts `files` so a spec-local mutator module can be generated.
Tests: 25 security + 37 functional hidden + 95 project tests (restored from pristine copies).
Oracle extended with `jsStringLiteralEscape` in the three metadata emitters and in combine's two
type-level argument lists.

## Gate (Frontier 1.4) — 2026-10-22
conformance: conforming; static PASSED; nop PASSED (25 security fail, 131 functional pass);
oracle PASSED 3/3 at reward 1.0; patches PASSED (all 23 checks as declared).
