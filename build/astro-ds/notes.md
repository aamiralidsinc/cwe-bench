# astro-ds — build notes (build-v1, pattern A, injected track)

Start (UTC): 2026-10-18T21:58Z. End: see end_utc.txt.

## Advisory / pin
GHSA-8MV7-9C27-98VC / CVE-2026-73423 — withastro/astro, CWE-352 (missing origin check on
alternate request-pipeline composition). Pinned `79aa99c648b4b40b95a31d4a961b77074cf7963c`,
verified with the GitHub API as the direct parent of the published fix
`0b30b35f864310bee8485c952d1877e82e2b9b1a` (2026-10-18). Track INJECTED. The published
regression tests (`test/units/actions/action-origin-check.test.ts`,
`test/units/hono/pages-origin-check.test.ts`) are absent at the pin.

## Mechanism (one line)
When the origin check is enabled, a non-safe form-like (or content-type-less) cross-site request
must not reach an action, endpoint or page; at the pin the decision lives only in the
middleware chain, so any dispatch path composed outside that chain runs the handler.

## Plan (written before building)

### Levers from the published fix (pattern A)
- T1 (landing): action execution — the report's RPC/form action path. `actions/handler.ts`.
  Dismiss: none (reported).
- T2 (far site): page/endpoint dispatch without the middleware step.
  `core/pages/handler.ts` (handleWithErrorFallback). Dismiss: `middleware()` looks mandatory.
- T3 (input shapes): non-safe methods, all three form content types in any case/with parameters,
  missing content type, missing Origin, RPC vs form action. Dismiss: a hand-rolled check for the
  reported POST/urlencoded case looks complete.
- T4 (coupled): same-site submissions, cross-site JSON, GET/HEAD/OPTIONS, `checkOrigin: false`
  must keep working (functional tests).
- T5 (far site, lower-level API): the `astro/fetch` primitives under the Hono wrapper. Dismiss:
  the report names `astro/hono`. (Same as T2's second entry point.)

### Injected siblings (recurring trust decision: "may this request reach the handler?")
Each is a composable primitive added to `astro/fetch` + `astro/hono`, the same shape a maintainer
uses for every new pipeline feature; none is touched by the published fix.
- S1 `endpoints(state)` — API-only dispatcher. Renders the matched endpoint by calling
  `renderEndpoint` itself, without the middleware chain or the shared dispatch class.
  Dismiss: "endpoints are dispatched by `pages()`; this is a convenience for API-only hosts".
- S2 `formActions(state)` — runs a form action for hosts that render HTML themselves
  (`getActionContext` + handler), then continues.
  Dismiss: "all action execution goes through the action-handler class".
- S3 `partials(state)` — renders a page route for fragment updates. It carries a hand-rolled
  origin check that only covers `POST` with the exact `application/x-www-form-urlencoded` string.
  Dismiss: "this primitive already has an origin check".

Distinct reasons to skip: reported-only / pages()-covers-dispatch / centralized-action-handler /
a-check-is-already-there.

### Coupled behaviour per lever
- S1: same-site form POST/PUT/DELETE reaches the endpoint; cross-site JSON POST reaches it;
  GET/HEAD/OPTIONS reach it; checkOrigin:false lets a cross-site form POST through.
- S2: same-site form actions run; cross-site JSON actions are unaffected; checkOrigin:false runs.
- S3: same-site multipart/PUT renders the page; cross-site JSON renders it; safe methods render;
  checkOrigin:false lets a cross-site PUT through.
Plus the base functional suite (same-site through hono/fetch, JSON, safe methods, checkOrigin
false, App.render reference behaviour) and the project's own unit tests for hono/fetch/actions/
middleware.

### Out of scope (one line each, not built on)
- Manifest without a middleware loader (edge-middleware mode) skips the check on the standard
  path; whether edge adapters check elsewhere was not traced.
- The container API hard-codes `checkOrigin: false`; intentional for a render API.

## Verified
- Pinned commit: `79aa99c6` is the direct parent of `0b30b35f` (GitHub commits API, read-only,
  2026-10-18). Injection patch applies with `patch -p1 --dry-run` to the pinned tree.
- Published regression tests are absent at the pin (`test/units/actions/action-origin-check.test.ts`,
  `test/units/hono/pages-origin-check.test.ts`).
- Pinned+injected (local dev image): security 0/20 pass (all fail with the handler having run),
  functional 165/165 pass. Oracle (published fix + guards at all three injected sites):
  security 20/20, functional 165/165. The `nop` gate stage confirmed this on the built image
  (security 20, functional 165).
- Every `checks/*.patch` was applied to the pinned+injected tree, rebuilt and run locally:
  - the five `sf_miss_*` patches each leave only their lever's security tests failing and all
    165 functional tests passing;
  - `sf_post_only`, `sf_exact_content_type`, `sf_absent_origin_allowed`, `sf_rpc_actions_only`,
    `sf_check_after_action`, `sf_throw_instead_of_refusal` behave as declared;
  - the three `ff_*` patches fail functional tests;
  - `pass_hardening` and `pass_alt_fetch_primitives` score 1.0 (20/20, 165/165).
- The project unit tests for hono, fetch, actions and middleware (part of the functional group)
  pass on pinned+injected and on the oracle. `test/units/app/csrf.test.ts` stays excluded because
  it imports the module the upstream fix renames.
- Hidden tests are not in the image; `environment/` holds only the Dockerfile and the injection
  patch, which shares no distinctive line with `tests/` (static gate re-checked).
- Gate stages: `nop` PASSED (20 security fail / 165 functional pass). Oracle stage PASSED
  (3 runs, reward 1.0 each, 20/20 + 165/165). `patches` was re-run several times because the
  shared VM returned Docker-compose / egress-control infrastructure errors on individual
  trials; completed trials matched the local results exactly (every `sf_*` check had
  165/165 functional and only its own security class failing), and the stage was not treated
  as a task failure.

## Could not verify / scope notes
- Prerendered routes as a coupled behaviour: an on-demand App does not match prerendered routes
  (404), so the composable entry points cannot reach them. Not tested (same as the base task).
- Project test `test/units/app/csrf.test.ts` was excluded: it imports the module the upstream
  fix renames.
- Out of scope (screener O8, one line): when the manifest has no middleware loader
  (edge-middleware mode) the standard path skips the check; whether edge adapters check elsewhere
  was not traced. Not built on.
- Out of scope: the container API hard-codes `checkOrigin: false`; intentional for a render API.
- Not measured: how much the injected siblings actually cost the target models (trials are run
  downstream, not here). The task is reported as built on the gate result; if the downstream
  trials miss the bar, it must be reported as such.



## End
End (UTC): see the timestamp above. Gate result: static (only `checks/blind.patch` and
`build/astro-ds/FAIRNESS.md` outstanding, written downstream), `nop` PASSED (security 20,
functional 165), `oracle` PASSED (3 runs, reward 1.0), `patches` PASSED (16/16; the stage was
re-run after two Docker-compose/egress-control infrastructure errors on the shared VM; the
completed trials and the final clean run matched the local results).

## Hardening pass (2026-10-21, Frontier 1.4)

Why: both target models solved the built task; the trial summary shows every existing trap fixed by
the solving run. Two new fair levers were added, each through a public request-handling building
block (`astro/fetch` + `astro/hono`), and the task was converted to the Frontier delivery format.

- N1 `rewrite()` (core/rewrites/rewrite-handler.ts): a host keeping a legacy URL alive mounts a
  rewrite step that resolves the target and dispatches the rewritten page/endpoint itself, without
  the middleware chain. Dismiss: "a rewrite only changes the destination; the check already ran".
  Fixed by a check in the helper, in the shared page dispatch, or at the fetch wrapper.
- N2 `fragments()` (core/pages/fragment-handler.ts): a fragment renderer calls `renderPage`
  directly, outside the page/endpoint dispatcher, so a dispatcher-only fix never reaches it.
  Dismiss: "a view helper, not a request entry point". Independent of N1: a run that guards only
  the dispatcher passes N1 and still fails N2.

Each lever has its own `security_fail` patch (sf_miss_rewrites, sf_miss_fragments) and coupled
functional tests (same-site, cross-site JSON, safe methods, `checkOrigin:false`). 9 new security
tests (29 total) and 9 new functional tests (174 total). Local validation on the pinned+injected
tree: nop 0/29 security + 174/174 functional; oracle 29/29 + 174/174; every regenerated check patch
behaves as declared.

Delivery: `/workspace` everywhere, separate offline verifier, artifact restore with `node_modules`
and `dist` excluded, a pristine pnpm dependency tree overlaid at grade time (hardlinked) and both
the workspace dependencies and `astro` rebuilt as uid-1000 `agent`; fresh one-commit git baseline;
canary GUID; B7 metadata. `conformance_check.py` prints conforming.

## Final gate (2026-10-21)

- `conformance_check.py tasks/astro-ds` -> conforming.
- `gate.py astro-ds --only static` -> PASSED.
- `gate.py astro-ds --only nop` -> PASSED: 29 security tests all fail on pinned+injected, 174/174
  functional pass (scene `[run] nop attempt 1 rc=0 22:49:12`).
- `gate.py astro-ds --only oracle` -> PASSED: 3 trials, reward 1.0 each (29/29 + 174/174).
- `gate.py astro-ds --only patches` -> PASSED: 19/19 check patches (17 old + sf_miss_rewrites and
  sf_miss_fragments; pass_hardening, pass_alt_fetch_primitives and blind all 1.0).
- Verifier mechanics were also simulated standalone (docker build of tests/Dockerfile + /tests/test.sh
  over a `git archive` artifact): nop reward 0.0 with 0/29 security + 174/174 functional, oracle
  reward 1.0 with 29/29 + 174/174.

The verifier binds `/opt/astro-pristine/node_modules` at `/workspace/node_modules` and copies each
workspace package's own `node_modules` (including the nested packages/markdown, packages/language-
tools and scripts ones) so the agent's sources are graded while the third-party dependency tree,
which is excluded from the artifact, comes from the image.
