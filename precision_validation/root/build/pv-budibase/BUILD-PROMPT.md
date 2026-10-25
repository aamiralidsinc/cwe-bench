# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-budibase`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-MQHR-6J6H-74P5", "CVE-2026-73407"]; budibase/budibase; credential/secret exposure to attacker-chosen origin (CWE-200; SSRF-adjacent origin confinement of outbound requests)
- Pinned (vulnerable) commit: parent of 8b1bca71501b11c68310351ef4f2c3028b2d5f08 (parent_commit not supplied; tree at /home/mara/screen3/hosts/12672/repo). Published fix: 8b1bca71501b11c68310351ef4f2c3028b2d5f08.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "12672",
 "advisory_ids": [
  "GHSA-MQHR-6J6H-74P5",
  "CVE-2026-73407"
 ],
 "repo": "budibase/budibase",
 "pinned_commit": "parent of 8b1bca71501b11c68310351ef4f2c3028b2d5f08 (parent_commit not supplied; tree at /home/mara/screen3/hosts/12672/repo)",
 "fix_commits": [
  "8b1bca71501b11c68310351ef4f2c3028b2d5f08"
 ],
 "trust_decision": {
  "summary": "Before attaching datasource-scoped secrets (defaultHeaders, authConfigs Basic/Bearer/apiKey/OAuth2), RestIntegration._req must decide the outbound URL (after query-parameter substitution, and after any redirect) stays on the datasource's origin; at the pinned commit it attaches secrets without any origin check, and on cross-origin redirects fetchWithBlacklist strips only authorization/cookie headers, so custom secret headers follow.",
  "evidence": [
   "packages/server/src/integrations/rest.ts:674-680",
   "packages/server/src/integrations/rest.ts:396-404",
   "packages/server/src/integrations/rest.ts:719-724",
   "packages/backend-core/src/utils/outboundFetch.ts:9-14",
   "packages/backend-core/src/utils/outboundFetch.ts:241-243",
   "packages/server/src/threads/query.ts:193",
   "fix.diff:341-358",
   "fix.diff:391"
  ]
 },
 "landing_point": {
  "where": "packages/server/src/integrations/rest.ts:660",
  "why": "The summary names REST datasource credentials; RestIntegration._req is where datasource headers/auth are merged and the URL is built."
 },
 "fix_sites": [
  {
   "where": "packages/server/src/integrations/rest.ts:660",
   "entry_point": "POST /api/queries/preview, POST /api/queries/:queryId, POST /api/v2/queries/:queryId (via threads/query.ts QueryRunner -> integration[verb] -> _req); fix.diff:332-391 adds getOrigin/assertSameOrigin and moves URL build before auth headers",
   "module_kind": "integration (primary, landing point)"
  },
  {
   "where": "packages/server/src/integrations/rest.ts:764-778",
   "entry_point": "same query routes; fix.diff:423 passes rejectCrossOriginRedirects: true",
   "module_kind": "integration call into shared lower-level fetch"
  },
  {
   "where": "packages/server/src/integrations/rest.ts:349-352",
   "entry_point": "same query routes; fix.diff:320-326 gives getUrl default args so it can compute the bare base origin",
   "module_kind": "integration helper"
  },
  {
   "where": "packages/backend-core/src/utils/outboundFetch.ts:241",
   "entry_point": "public library API coreUtils.fetchWithBlacklist (backend-core), reached by REST queries; fix.diff:5-29 adds opt-in rejectCrossOriginRedirects",
   "module_kind": "lower-level shared API in another package"
  },
  {
   "where": "packages/server/src/threads/query.ts:193",
   "entry_point": "QueryRunner.execute (query thread) for every query route; fix.diff:457-461 captures pre-substitution fields.path as rawPath for REST",
   "module_kind": "query runner / templating layer (different layer from integration)"
  },
  {
   "where": "packages/types/src/documents/workspace/query.ts:85",
   "entry_point": "type only (RestQueryFields.rawPath); fix.diff:473-474",
   "module_kind": "types package"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "packages/backend-core/src/utils/outboundFetch.ts:241-243 (redirect handling in shared fetchWithBlacklist; existing defence strips only the headers listed at packages/backend-core/src/utils/outboundFetch.ts:9-14, so datasource defaultHeaders / apiKey headers survive a cross-origin redirect). Second out-of-layer site: packages/server/src/threads/query.ts:193 where the pre-template path must be preserved."
 },
 "O3_reason_to_dismiss": "fetchWithBlacklist already strips sensitive headers on cross-origin redirects (outboundFetch.ts:241-243) and is a shared SSRF utility in backend-core used by automations/plugins, so a solver can argue redirects are 'already handled' and out of the REST integration's scope.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Relative paths, absolute paths on the datasource origin, and same-origin redirects must keep working (fix.diff:186-201, fix.diff:292-307); other fetchWithBlacklist callers (automation webhook/n8n/make/zapier steps, OAuth2 token fetch, plugin downloads) must keep following cross-origin redirects, so the reject is opt-in defaulting false (fix.diff:17). Also a datasource with no base URL using a static absolute path must keep working (only rawPath origin compared, fix.diff:345-350).",
  "where": "packages/server/src/automations/steps/utils.ts:28-35; packages/backend-core/src/utils/outboundFetch.ts:178-185; packages/server/src/integrations/rest.ts:399-401"
 },
 "O6_input_shapes": [
  "absolute path in fields.path to a different host",
  "templated path ({{ t }}) whose parameter resolves to a different host",
  "different port, same host",
  "different scheme, same host",
  "datasource base URL without a scheme (getUrl prefixes http://)",
  "same-origin request whose response redirects (3xx Location) to a different origin",
  "secrets as custom defaultHeaders (not stripped by redirect list) and as Bearer authConfig"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "packages/server/src/threads/query.ts:193 (sdk.queries.enrichContext substitutes parameters into fields.path before the integration sees it)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "OAuth2 token request for datasource/inline OAuth2 authConfigs sends client_secret in the POST body via fetchWithBlacklist without rejectCrossOriginRedirects; 307/308 redirects keep the body cross-origin (only the Authorization header is stripped).",
   "where": "packages/server/src/sdk/workspace/oauth2/utils.ts:56-68",
   "reason_to_dismiss": "Token URL is builder-configured OAuth2 config, not the query path, and is a neighbouring feature (OAuth2 configs) rather than the REST request itself.",
   "distance": "different package dir (server/src/sdk/workspace/oauth2) from integrations/rest.ts; reached from rest.ts:639 and rest.ts:654 via getAuthHeaders",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/server/src/sdk/workspace/oauth2/utils.ts:68"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/server/src/integrations/rest.ts:327-329",
   "sibling": "cursor pagination that accepts a full 'next' URL from the response (responseParam) as the next request path, re-sending datasource headers",
   "why_realistic": "Many APIs return absolute next-page links; a maintainer adding link-style pagination would reuse _req with that URL and not re-check origin."
  },
  {
   "where": "packages/server/src/integrations/rest.ts:813-817",
   "sibling": "a retry/refresh path (e.g. 401 retry with re-fetched token or a 'test connection' helper) that builds its own URL and calls fetchWithBlacklist directly, bypassing assertSameOrigin",
   "why_realistic": "The retry already re-enters _req; a maintainer optimising it into a direct fetch is plausible."
  },
  {
   "where": "packages/server/src/sdk/workspace/oauth2/utils.ts:68",
   "sibling": "token endpoint fetch without rejectCrossOriginRedirects",
   "why_realistic": "Already exists at the pinned commit (O8); it is a natural second credential-bearing call."
  }
 ],
 "O9_family": "credential/secret exposure to attacker-chosen origin (CWE-200; SSRF-adjacent origin confinement of outbound requests)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node.js)",
  "toolchain": "yarn workspaces + nx/lerna monorepo, jest",
  "services": [
   "CouchDB (testcontainers, globalSetup.ts:79)",
   "MinIO (testcontainers, globalSetup.ts:115)",
   "Docker for testcontainers"
  ],
  "offline_after_build": true,
  "project_tests": "packages/server/src/api/routes/tests/queries/rest.spec.ts (route-level, undici MockAgent), packages/server/src/integrations/tests/rest.spec.ts (unit), packages/backend-core/src/utils/tests/outboundFetch.spec.ts (unit)"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/server/src/integrations/rest.ts, packages/backend-core/src/utils/outboundFetch.ts, packages/server/src/threads/query.ts, packages/types/src/documents/workspace/query.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "In rest.ts _req, compare the built URL's host with config.url and throw; this misses redirects (custom headers survive outboundFetch's strip list), datasources with no base URL (needs pre-template rawPath from threads/query.ts), and port/scheme variants if comparing hostname only."
 },
 "out_of_scope_notes": [
  "outboundFetch strip list (outboundFetch.ts:9-14) lets custom secret headers in automation webhook/n8n/make steps follow cross-origin redirects; builder-authored, not datasource credentials.",
  "Template datasource base-URL rewrite (threads/query.ts:130-142, applyBaseUrl) runs before rawPath capture; not analysed further."
 ],
 "unverified": [
  "repo_mb not measured (no shell); budibase monorepo assumed between 5 MB and 1.5 GB.",
  "Advisory text itself not provided; trust decision derived from summary and fix diff.",
  "Whether 'unauthenticated' relies on QUERY permission set to PUBLIC role for execute routes (routes/query.ts:25-31) not confirmed.",
  "Whether templated config.url (restTemplate datasources) is resolved before assertSameOrigin's getUrl() not checked.",
  "Exact public API route path for query execute (controllers/public/queries.ts:15 calls executeV2) not traced to router line.",
  "Whether unit tests in packages/server can run without the testcontainers globalSetup not checked."
 ]
}
  ```
- Published fix sites:   - packages/server/src/integrations/rest.ts:660 — entry point: POST /api/queries/preview, POST /api/queries/:queryId, POST /api/v2/queries/:queryId (via threads/query.ts QueryRunner -> integration[verb] -> _req); fix.diff:332-391 adds getOrigin/assertSameOrigin and moves URL build before auth headers [integration (primary, landing point)]
  - packages/server/src/integrations/rest.ts:764-778 — entry point: same query routes; fix.diff:423 passes rejectCrossOriginRedirects: true [integration call into shared lower-level fetch]
  - packages/server/src/integrations/rest.ts:349-352 — entry point: same query routes; fix.diff:320-326 gives getUrl default args so it can compute the bare base origin [integration helper]
  - packages/backend-core/src/utils/outboundFetch.ts:241 — entry point: public library API coreUtils.fetchWithBlacklist (backend-core), reached by REST queries; fix.diff:5-29 adds opt-in rejectCrossOriginRedirects [lower-level shared API in another package]
  - packages/server/src/threads/query.ts:193 — entry point: QueryRunner.execute (query thread) for every query route; fix.diff:457-461 captures pre-substitution fields.path as rawPath for REST [query runner / templating layer (different layer from integration)]
  - packages/types/src/documents/workspace/query.ts:85 — entry point: type only (RestQueryFields.rawPath); fix.diff:473-474 [types package]
- Uncovered routes to confirm (pattern B):   - packages/server/src/sdk/workspace/oauth2/utils.ts:56-68 — OAuth2 token request for datasource/inline OAuth2 authConfigs sends client_secret in the POST body via fetchWithBlacklist without rejectCrossOriginRedirects; 307/308 redirects keep the body cross-origin (only the Authorization header is stripped). (reason to dismiss: Token URL is builder-configured OAuth2 config, not the query path, and is a neighbouring feature (OAuth2 configs) rather than the REST request itself.; still in latest: yes)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-budibase/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/pv-budibase/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/pv-budibase/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/pv-budibase/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/pv-budibase/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-budibase/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/pv-budibase/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-budibase --only static
python3 -I builder/gate.py pv-budibase --only nop
python3 -I builder/gate.py pv-budibase --only oracle
python3 -I builder/gate.py pv-budibase --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-budibase/`;
  - edit only `tasks/pv-budibase/`, `build/pv-budibase/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
