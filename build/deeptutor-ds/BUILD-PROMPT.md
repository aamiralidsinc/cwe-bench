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

Project root: `/home/mara/cwe-bench`. Task: `deeptutor-ds`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-JG88-RVPC-QVXJ", "CVE-2026-58168"]; hkuds/deeptutor; missing authorization (CWE-862), default-allow per-user tool whitelist
- Pinned (vulnerable) commit: 86ff120668c92c2d9a67d4570df636b8167b770c. Published fix: 90046374b3dcd4f8a866d2d64a64440bc08eb2ef.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "4154",
 "advisory_ids": [
  "GHSA-JG88-RVPC-QVXJ",
  "CVE-2026-58168"
 ],
 "repo": "hkuds/deeptutor",
 "pinned_commit": "86ff120668c92c2d9a67d4570df636b8167b770c",
 "fix_commits": [
  "90046374b3dcd4f8a866d2d64a64440bc08eb2ef"
 ],
 "trust_decision": {
  "summary": "Whether a non-admin user may list/load/run a given MCP (deferred) tool is decided by allowed_mcp_tools() reading the user's grant, where a missing grant or mcp_tools=None means unrestricted; the chat pipeline then filters the deferred pool and DeferredToolLoader with that set.",
  "evidence": [
   "deeptutor/multi_user/tool_access.py:27-32",
   "deeptutor/multi_user/tool_access.py:46-54",
   "deeptutor/multi_user/grants.py:29-31",
   "deeptutor/multi_user/grants.py:74-81",
   "deeptutor/agents/chat/agentic_pipeline.py:440-459",
   "deeptutor/runtime/registry/deferred_tools.py:89-93"
  ]
 },
 "landing_point": {
  "where": "deeptutor/multi_user/tool_access.py:46",
  "why": "allowed_mcp_tools() is the named per-user MCP whitelist; returning None for absent grants is the 'missing authorization' the summary describes."
 },
 "fix_sites": [
  {
   "where": "deeptutor/multi_user/tool_access.py:46",
   "entry_point": "chat turn (WS /api/v1 unified_ws, POST chat router, cron chat job) -> AgenticChatPipeline._prepare_deferred_tools",
   "module_kind": "authorization helper (inferred site; diff has no hunks)"
  },
  {
   "where": "deeptutor/multi_user/tool_access.py:27",
   "entry_point": "same as above; _current_grant also feeds allowed_optional_tools/exec_override",
   "module_kind": "authorization helper (inferred site)"
  },
  {
   "where": "deeptutor/multi_user/grants.py:30",
   "entry_point": "PUT /api/v1/multi-user/users/{user_id}/grants (save) and every load_grant() caller",
   "module_kind": "grant defaults / normalisation (inferred site)"
  },
  {
   "where": "deeptutor/multi_user/grants.py:67-68",
   "entry_point": "normalize_grant via load_grant/save_grant (v1->v2 migration)",
   "module_kind": "grant defaults / normalisation (inferred site)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "deeptutor/multi_user/grants.py:16-32 (empty_grant default mcp_tools=None) and deeptutor/multi_user/grants.py:74-81 (missing or corrupt grant file falls back to empty_grant); v1 migration documents absent v2 fields as unrestricted at deeptutor/multi_user/grants.py:51-53"
 },
 "O3_reason_to_dismiss": "The playground tool-execute endpoint is a developer 'Playground tester' (deeptutor/api/routers/plugins_api.py:5-6,116), not the chat grant path the report describes, so a solver can argue it is a separate debugging feature that sits outside per-user grants.",
 "O4_distance": {
  "files": 4,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Partner turns run as a synthetic role='user' identity with no grant file and get their MCP whitelist from mcp_tools_filter; a blanket 'deny MCP when no grant' for every non-admin breaks partners' configured MCP tools. Admins stay unrestricted, and an explicit grant list must keep working.",
  "where": "deeptutor/services/partners/scope.py:32-39; deeptutor/multi_user/tool_access.py:5-7; deeptutor/services/partners/runtime.py:416-418; deeptutor/agents/chat/agentic_pipeline.py:442-446"
 },
 "O6_input_shapes": [
  "no grant file (deeptutor/multi_user/grants.py:76-77)",
  "unreadable/corrupt grant file (deeptutor/multi_user/grants.py:80-81)",
  "grant with mcp_tools absent or null, including v1 grants (deeptutor/multi_user/grants.py:67-68)",
  "grant with mcp_tools of a non-list type, normalised to None (deeptutor/multi_user/grants.py:38-39)",
  "explicit [] vs explicit list (deeptutor/multi_user/grants.py:40)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "deeptutor/multi_user/grants.py:48-81 (normalize_grant/load_grant produce mcp_tools=None by default)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "Authenticated non-admin calls POST /api/v1/plugins/tools/{tool_name}/execute, which runs any registry tool, MCP adapters included, with no grant check",
   "where": "deeptutor/api/routers/plugins_api.py:114-123",
   "reason_to_dismiss": "Documented as a Playground tester endpoint, not the chat path; the router is mounted with _auth only (deeptutor/api/main.py:422-424)",
   "distance": "different package (deeptutor/api/routers) from deeptutor/multi_user and deeptutor/agents/chat",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Same as above via the SSE variant POST /api/v1/plugins/tools/{tool_name}/execute-stream",
   "where": "deeptutor/api/routers/plugins_api.py:207-241",
   "reason_to_dismiss": "Same playground feature; it falls together with the route above",
   "distance": "same file as previous route",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Chat tool dispatch executes any registered tool name the LLM emits, with no check against the turn's schema list or the loader's allowed set, so the MCP grant is enforced only at listing/loading time",
   "where": "deeptutor/core/agentic/tool_dispatch.py:104-160; deeptutor/core/agentic/tool_dispatch.py:376-381; deeptutor/runtime/registry/tool_registry.py:138-151",
   "reason_to_dismiss": "The model only sees granted schemas and the manifest says direct calls 'will fail' (deeptutor/runtime/registry/deferred_tools.py:47-52); calling an unlisted name looks like a model-misbehaviour issue, not authorization",
   "distance": "deeptutor/core/agentic package, two packages away from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Non-admin uses POST /api/v1/plugins/capabilities/chat/execute-stream with bot_id to drive an admin-owned partner chat, which runs as the grantless partner identity with the partner's MCP tools",
   "where": "deeptutor/api/routers/plugins_api.py:291-320",
   "reason_to_dismiss": "Partner management is a neighbouring, admin-gated feature (deeptutor/api/main.py:428-430); this looks like a partner-gate issue, not a user-grant one",
   "distance": "deeptutor/api/routers to deeptutor/services/partners",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "deeptutor/agents/chat/agentic_pipeline.py:442-449",
   "sibling": "a second capability or pipeline (e.g. research) that builds its own deferred pool from registry.deferred_tools() without calling allowed_mcp_tools",
   "why_realistic": "Pool construction is a few lines that are easy to copy; registry.deferred_tools() is public (deeptutor/runtime/registry/tool_registry.py:45-47)"
  },
  {
   "where": "deeptutor/runtime/registry/deferred_tools.py:103-119",
   "sibling": "session-persisted loaded tools (load_loaded_tools) replayed into schemas by a path that skips _is_allowed, e.g. a resume or history rebuild",
   "why_realistic": "Loaded names cross a save/reload boundary through services/mcp/session_state; a maintainer adding a resume path could trust persisted state"
  }
 ],
 "O9_family": "missing authorization (CWE-862), default-allow per-user tool whitelist",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "pip/pyproject + pytest (FastAPI app)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/multi_user/test_tool_access.py, tests/runtime/registry/test_deferred_tools.py, tests/services/mcp/test_mcp_config.py"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "unknown (diff has no hunks); inferred deeptutor/multi_user/tool_access.py, deeptutor/multi_user/grants.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Make allowed_mcp_tools() return set() whenever the grant lacks mcp_tools, which leaves the playground execute routes open and breaks partner MCP tools"
 },
 "out_of_scope_notes": [
  "The playground capability route lets non-admins drive admin-gated partners (deeptutor/api/routers/plugins_api.py:296-318 vs deeptutor/api/main.py:428-430); this is a partner-gate issue beyond MCP.",
  "The playground tool-execute routes also expose non-MCP builtin tools (exec, code_execution) without the exec_override or enabled_tools grant checks (deeptutor/api/routers/plugins_api.py:114-123)."
 ],
 "unverified": [
  "The fix diff at scr-4154.fix.diff holds only the merge-commit header (fix.diff:1-2) with no hunks. The fix sites, changed files and input shapes are inferred from the pinned code, the commit title 'deny MCP tools until explicitly granted' and c_fix_sites=4/c_site_files=2. Fetch the real diff before using this host.",
  "Whether the published fix touched plugins_api.py or tool_dispatch.py is unknown; if it did, those O8 routes become fix sites (Pattern A).",
  "regression_tests_in_pinned_commit could not be checked without diff test files; the pinned tests assert the opposite (no grant = unrestricted) at tests/multi_user/test_tool_access.py:76-80.",
  "Repo size in MB not measured.",
  "No latest release given; present_in_latest is unknown for all routes.",
  "Not checked: whether require_auth enforces a logged-in non-admin on the plugins router when AUTH_ENABLED=true (deeptutor/api/main.py:346-350 states it does)."
 ]
}
  ```
- Published fix sites:   - deeptutor/multi_user/tool_access.py:46 — entry point: chat turn (WS /api/v1 unified_ws, POST chat router, cron chat job) -> AgenticChatPipeline._prepare_deferred_tools [authorization helper (inferred site; diff has no hunks)]
  - deeptutor/multi_user/tool_access.py:27 — entry point: same as above; _current_grant also feeds allowed_optional_tools/exec_override [authorization helper (inferred site)]
  - deeptutor/multi_user/grants.py:30 — entry point: PUT /api/v1/multi-user/users/{user_id}/grants (save) and every load_grant() caller [grant defaults / normalisation (inferred site)]
  - deeptutor/multi_user/grants.py:67-68 — entry point: normalize_grant via load_grant/save_grant (v1->v2 migration) [grant defaults / normalisation (inferred site)]
- Uncovered routes to confirm (pattern B):   - deeptutor/api/routers/plugins_api.py:114-123 — Authenticated non-admin calls POST /api/v1/plugins/tools/{tool_name}/execute, which runs any registry tool, MCP adapters included, with no grant check (reason to dismiss: Documented as a Playground tester endpoint, not the chat path; the router is mounted with _auth only (deeptutor/api/main.py:422-424); still in latest: unknown)
  - deeptutor/api/routers/plugins_api.py:207-241 — Same as above via the SSE variant POST /api/v1/plugins/tools/{tool_name}/execute-stream (reason to dismiss: Same playground feature; it falls together with the route above; still in latest: unknown)
  - deeptutor/core/agentic/tool_dispatch.py:104-160; deeptutor/core/agentic/tool_dispatch.py:376-381; deeptutor/runtime/registry/tool_registry.py:138-151 — Chat tool dispatch executes any registered tool name the LLM emits, with no check against the turn's schema list or the loader's allowed set, so the MCP grant is enforced only at listing/loading time (reason to dismiss: The model only sees granted schemas and the manifest says direct calls 'will fail' (deeptutor/runtime/registry/deferred_tools.py:47-52); calling an unlisted name looks like a model-misbehaviour issue, not authorization; still in latest: unknown)
  - deeptutor/api/routers/plugins_api.py:291-320 — Non-admin uses POST /api/v1/plugins/capabilities/chat/execute-stream with bot_id to drive an admin-owned partner chat, which runs as the grantless partner identity with the partner's MCP tools (reason to dismiss: Partner management is a neighbouring, admin-gated feature (deeptutor/api/main.py:428-430); this looks like a partner-gate issue, not a user-grant one; still in latest: unknown)
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

## Environment (`tasks/deeptutor-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/deeptutor-ds/instruction.md`)
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

## Tests (`tasks/deeptutor-ds/tests/`)
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
- **Wrong-fix patches** go in `build/deeptutor-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/deeptutor-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/deeptutor-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/deeptutor-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py deeptutor-ds --only static
python3 -I builder/gate.py deeptutor-ds --only nop
python3 -I builder/gate.py deeptutor-ds --only oracle
python3 -I builder/gate.py deeptutor-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/deeptutor-ds/`;
  - edit only `tasks/deeptutor-ds/`, `build/deeptutor-ds/` and, for pattern B, the register;
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
