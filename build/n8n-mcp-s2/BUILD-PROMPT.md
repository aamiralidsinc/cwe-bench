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

Project root: `/home/mara/cwe-bench`. Task: `n8n-mcp-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2CF7-HPWF-47H9", "CVE-2026-55608"]; czlonkowski/n8n-mcp; incorrect authorization / broken tenant scoping exposing stored data (CWE-863, CWE-200)
- Pinned (vulnerable) commit: b0f5e25d22c1e28363c27aee160518c301341edc. Published fix: c1ca1e73697feaec5ec2a5fb7e6992a2892b62c9.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "7471",
 "advisory_ids": [
  "GHSA-2CF7-HPWF-47H9",
  "CVE-2026-55608"
 ],
 "repo": "czlonkowski/n8n-mcp",
 "pinned_commit": "b0f5e25d22c1e28363c27aee160518c301341edc",
 "fix_commits": [
  "c1ca1e73697feaec5ec2a5fb7e6992a2892b62c9"
 ],
 "trust_decision": {
  "summary": "In multi-tenant HTTP mode the /mcp route is the trust decision: it admits a request that carries only one of X-n8n-url / X-n8n-key (the gate rejects only when both are absent), getInstanceScopeId then returns the empty default tenant key '' for that partial context, and handleWorkflowVersions uses that key unguarded for list/get/rollback/delete, so a tenant reads and deletes the operator's default-scope workflow_versions rows; the fix requires both tenant headers at the transport and separately fails closed in the handler when ENABLE_MULTI_TENANT is true and the derived scope is ''.",
  "evidence": [
   "src/http-server-single-session.ts:1338-1341",
   "src/types/instance-context.ts:140-178",
   "src/types/instance-context.ts:223-231",
   "src/mcp/handlers-n8n-manager.ts:2401-2409",
   "src/database/node-repository.ts:1135-1160",
   "fix.diff:144",
   "fix.diff:164"
  ]
 },
 "landing_point": {
  "where": "src/http-server-single-session.ts:1341",
  "why": "The advisory summary is about authorization in multi-tenant HTTP mode; this is the only multi-tenant tenant-header gate on POST /mcp, so anyone grepping ENABLE_MULTI_TENANT in the HTTP server lands on this condition and the one-word change `&&` -> `||`."
 },
 "fix_sites": [
  {
   "where": "src/http-server-single-session.ts:1338-1355",
   "entry_point": "POST /mcp (StreamableHTTP JSON-RPC endpoint of SingleSessionHTTPServer)",
   "module_kind": "http_transport"
  },
  {
   "where": "src/mcp/handlers-n8n-manager.ts:2401-2410",
   "entry_point": "n8n_workflow_versions tool handler (handleWorkflowVersions), reachable from every transport that dispatches MCP tools",
   "module_kind": "mcp_tool_handler"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/http-server.ts:195"
 },
 "O3_reason_to_dismiss": "The deprecated USE_FIXED_HTTP server (src/http-server.ts:4 tells readers to use SingleSessionHTTPServer instead, and src/mcp/index.ts:103-120 only reaches it behind an explicit env var with a deprecation warning) builds one process-wide context-less N8NDocumentationMCPServer and never reads ENABLE_MULTI_TENANT, so a solver can call it a legacy, non-SaaS path and leave it open.",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Single-user / stdio deployments legitimately run with the empty scope '': getInstanceScopeId returns '' when no credentials are present and the workflow_versions.instance_id column defaults to '' (src/database/schema.sql:240). A fix that rejects an empty derived scope unconditionally, instead of only under ENABLE_MULTI_TENANT, breaks their entire existing version history and every new backup, including n8n_update_partial_workflow's non-blocking backups.",
  "where": "src/types/instance-context.ts:216-231"
 },
 "O6_input_shapes": [
  "X-n8n-url present, X-n8n-key absent (URL-only partial context)",
  "X-n8n-key present, X-n8n-url absent (key-only partial context)",
  "neither tenant header (pre-existing GHSA-jxx9-px88-pj69 case, now also covered by the handler guard)",
  "X-instance-id only, no url/key",
  "both tenant headers present (must keep working, and must keep working for both MULTI_TENANT_SESSION_STRATEGY values)",
  "all tool modes list/get/rollback/delete/deleteAll/prune under each of the above contexts"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "src/types/instance-context.ts:223-231",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /sse + POST /messages: the SSE transport constructs its server with no instance context at all, so n8n_workflow_versions runs with the derived scope '' in multi-tenant mode and lists/reads/deletes default-scope backups",
   "where": "src/http-server-single-session.ts:866-871",
   "reason_to_dismiss": "The source itself states 'SSE sessions do not support multi-tenant context. The SaaS backend uses StreamableHTTP exclusively.' (src/http-server-single-session.ts:866-867) and marks SSE deprecated (src/http-server-single-session.ts:1153-1156), which is exactly the plausible reason to treat the route as out of scope.",
   "distance": "same file, ~200 lines above the fixed gate; the context-less server construction is ~470 lines away",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "USE_FIXED_HTTP=true server: a single process-wide N8NDocumentationMCPServer() with no context; tools/call dispatches n8n_workflow_versions straight into the handler, so every tenant shares scope ''",
   "where": "src/http-server.ts:195",
   "reason_to_dismiss": "Deprecated, opt-in legacy HTTP implementation (src/http-server.ts:4, src/mcp/index.ts:103-120) that never mentions multi-tenancy, so a solver can argue multi-tenant deployments cannot use it.",
   "distance": "a separate HTTP server implementation in another file; it never reads ENABLE_MULTI_TENANT, so an env-var grep does not find it",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "n8n_update_partial_workflow (and n8n_autofix_workflow, which forwards createBackup:true into it) still writes backups stamped with the '' default scope when the request context is incomplete in multi-tenant mode; only the read handler got the fail-closed guard",
   "where": "src/mcp/handlers-workflow-diff.ts:200-206",
   "reason_to_dismiss": "Backups here are explicitly best-effort and non-blocking (errors swallowed at src/mcp/handlers-workflow-diff.ts:214-220) and the advisory text is about exposing backups rather than writing them, so a solver can treat the write path as a different, benign behaviour.",
   "distance": "a different tool family in another file under src/mcp (update path vs versions path)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "n8n_update_full_workflow's pre-update backup writer also derives its scope from getInstanceScopeId(context) with no fail-closed check, so an incomplete context writes into the shared default scope",
   "where": "src/mcp/handlers-n8n-manager.ts:990-995",
   "reason_to_dismiss": "Same best-effort/non-blocking backup argument, and it sits in the very file the fix edited, so a solver may assume it was already reviewed and covered.",
   "distance": "same file as the fixed handler, ~1400 lines above it",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/mcp/handlers-n8n-manager.ts:1416",
   "sibling": "a fourth backup trigger that forwards createBackup:true into the partial-update path, which would need the same tenant-scope fail-closed rule",
   "why_realistic": "The table already enumerates three triggers (schema.sql:245-249) and autofix already re-enters the partial-update handler this way, so adding another trigger/route is a normal maintainer change."
  },
  {
   "where": "src/http-server-single-session.ts:1180",
   "sibling": "a second message-delivery endpoint (/messages for the legacy SSE transport) that would need the same tenant-header gate as /mcp",
   "why_realistic": "This file already carries two parallel transports side by side, and one of them was left without the multi-tenant gate."
  },
  {
   "where": "src/types/instance-context.ts:223",
   "sibling": "a second scope-derivation helper (for example keyed on instanceId, or one built from createCacheKey) used by some call sites but not others",
   "why_realistic": "The function's own docstring (src/types/instance-context.ts:208-222) explains why createCacheKey must not be used, showing alternative derivations were considered; a maintainer could plausibly add one for a new route."
  },
  {
   "where": "src/database/node-repository.ts:1262",
   "sibling": "a repository read whose WHERE clause omits instance_id (a stats/export/admin variant)",
   "why_realistic": "getVersionStorageStats is already a scope-wide aggregate next to the per-tenant reads, so a cross-workflow or export query without the predicate is a realistic addition."
  }
 ],
 "O9_family": "incorrect authorization / broken tenant scoping exposing stored data (CWE-863, CWE-200)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node + npm, tsc via tsconfig.build.json, vitest ^3.2.4, express 5, @modelcontextprotocol/sdk 1.28.0, zod, native better-sqlite3 ^11.10.0",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/unit/http-server/ssrf-gate.test.ts:385 (multi-tenant header omission, mocked req/res on POST /mcp), tests/integration/security/ghsa-j6r7-workflow-versions.test.ts:13 (cross-tenant workflow_versions isolation, in-memory TestDatabase), tests/unit/http-server/multi-tenant-support.test.ts; run with `npm run test:run` / `npm run test:integration` (no network needed for this area)."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/http-server-single-session.ts, src/mcp/handlers-n8n-manager.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Flip the existing gate at src/http-server-single-session.ts:1341 from `!hasUrl && !hasKey` to `!hasUrl || !hasKey`, rerun the header tests, and stop there."
 },
 "out_of_scope_notes": [
  "Adjacent protection not part of this advisory and not pursued: instance-context validation with the SSRF gate at src/http-server-single-session.ts:1374-1391 (GHSA-4ggg-h7ph-26qr).",
  "The fix commit also regenerates committed dist/ bundles, source maps, package-lock and package.runtime.json; only the two src/ files were counted as source changes."
 ],
 "unverified": [
  "repo_mb: no shell available to measure the checkout; 213 files under src/*.ts plus data/nodes.db and data/templates.db are present, so it is clearly above the 5 MB tiny threshold, but the exact size is unknown.",
  "Whether a real multi-tenant deployment actually exposes /sse to tenants: the route is registered unconditionally behind the same bearer token, but deployment configuration was not inspected.",
  "present_in_latest for every O8 route: no latest release was provided, so all are answered unknown."
 ]
}
  ```
- Published fix sites:   - src/http-server-single-session.ts:1338-1355 — entry point: POST /mcp (StreamableHTTP JSON-RPC endpoint of SingleSessionHTTPServer) [http_transport]
  - src/mcp/handlers-n8n-manager.ts:2401-2410 — entry point: n8n_workflow_versions tool handler (handleWorkflowVersions), reachable from every transport that dispatches MCP tools [mcp_tool_handler]
- Uncovered routes to confirm (pattern B):   - src/http-server-single-session.ts:866-871 — GET /sse + POST /messages: the SSE transport constructs its server with no instance context at all, so n8n_workflow_versions runs with the derived scope '' in multi-tenant mode and lists/reads/deletes default-scope backups (reason to dismiss: The source itself states 'SSE sessions do not support multi-tenant context. The SaaS backend uses StreamableHTTP exclusively.' (src/http-server-single-session.ts:866-867) and marks SSE deprecated (src/http-server-single-session.ts:1153-1156), which is exactly the plausible reason to treat the route as out of scope.; still in latest: unknown)
  - src/http-server.ts:195 — USE_FIXED_HTTP=true server: a single process-wide N8NDocumentationMCPServer() with no context; tools/call dispatches n8n_workflow_versions straight into the handler, so every tenant shares scope '' (reason to dismiss: Deprecated, opt-in legacy HTTP implementation (src/http-server.ts:4, src/mcp/index.ts:103-120) that never mentions multi-tenancy, so a solver can argue multi-tenant deployments cannot use it.; still in latest: unknown)
  - src/mcp/handlers-workflow-diff.ts:200-206 — n8n_update_partial_workflow (and n8n_autofix_workflow, which forwards createBackup:true into it) still writes backups stamped with the '' default scope when the request context is incomplete in multi-tenant mode; only the read handler got the fail-closed guard (reason to dismiss: Backups here are explicitly best-effort and non-blocking (errors swallowed at src/mcp/handlers-workflow-diff.ts:214-220) and the advisory text is about exposing backups rather than writing them, so a solver can treat the write path as a different, benign behaviour.; still in latest: unknown)
  - src/mcp/handlers-n8n-manager.ts:990-995 — n8n_update_full_workflow's pre-update backup writer also derives its scope from getInstanceScopeId(context) with no fail-closed check, so an incomplete context writes into the shared default scope (reason to dismiss: Same best-effort/non-blocking backup argument, and it sits in the very file the fix edited, so a solver may assume it was already reviewed and covered.; still in latest: unknown)
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
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/n8n-mcp-s2/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/n8n-mcp-s2/instruction.md`)
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

## Tests (`tasks/n8n-mcp-s2/tests/`)
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
- **Wrong-fix patches** go in `build/n8n-mcp-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/n8n-mcp-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/n8n-mcp-s2/manifest.json`:**
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

**Also in `build/n8n-mcp-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py n8n-mcp-s2 --only static
python3 -I common/gate/gate.py n8n-mcp-s2 --only nop
python3 -I common/gate/gate.py n8n-mcp-s2 --only oracle
python3 -I common/gate/gate.py n8n-mcp-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/n8n-mcp-s2/`;
  - edit only `tasks/n8n-mcp-s2/`, `build/n8n-mcp-s2/` and, for pattern B, the register;
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
