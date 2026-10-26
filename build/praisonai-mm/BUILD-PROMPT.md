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

Project root: `/home/mara/cwe-bench`. Task: `praisonai-mm`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-2GPF-2492-Q9JH", "CVE-2026-61435"]; mervinpraison/praisonai; authentication bypass: locality decision trusted from a client-controlled Host header (CWE-287/306/346)
- Pinned (vulnerable) commit: unknown (parent of 2a855c470077c7d2e2479a575f7ef7f548d51c33; parent_commit is null in the candidate). Published fix: 2a855c470077c7d2e2479a575f7ef7f548d51c33, 846568c7a5d8ce9e71e56e4c213f027c04909753.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "155",
 "advisory_ids": [
  "GHSA-2GPF-2492-Q9JH",
  "CVE-2026-61435"
 ],
 "repo": "mervinpraison/praisonai",
 "pinned_commit": "unknown (parent of 2a855c470077c7d2e2479a575f7ef7f548d51c33; parent_commit is null in the candidate)",
 "fix_commits": [
  "2a855c470077c7d2e2479a575f7ef7f548d51c33",
  "846568c7a5d8ce9e71e56e4c213f027c04909753"
 ],
 "trust_decision": {
  "summary": "verify_token in the Call API decides whether a request needs CALL_SERVER_TOKEN. At the pinned commit, PRAISONAI_CALL_AUTH=disabled returns early with no locality check while call.py binds 0.0.0.0. The supplied diff (2a855c4) adds a 'localhost only' check, but it reads the hostname from request.url, which comes from the client's Host header. That is the spoofable decision the advisory names. Latest code decides from the server-side env PRAISONAI_CALL_BIND_HOST instead.",
  "evidence": [
   "src/praisonai/praisonai/api/agent_invoke.py:32",
   "src/praisonai/praisonai/api/agent_invoke.py:42-43",
   "src/praisonai/praisonai/api/call.py:363",
   "fix.diff:419-421",
   "fix.diff:430-436"
  ]
 },
 "landing_point": {
  "where": "src/praisonai/praisonai/api/agent_invoke.py:35-43",
  "why": "The summary says 'Call API localhost-only authentication', and verify_token's PRAISONAI_CALL_AUTH=disabled branch is the only auth bypass in the Call API."
 },
 "fix_sites": [
  {
   "where": "fix.diff:410-452 (src/praisonai/praisonai/api/agent_invoke.py:31-51)",
   "entry_point": "HTTP POST /api/v1/agents/{agent_id}/invoke, GET /api/v1/agents, POST /api/v1/agents/{agent_id}/register, DELETE /api/v1/agents/{agent_id}, GET /api/v1/agents/{agent_id} (all Depends(verify_token)), mounted by `praisonai call` (call.py:61) and `praisonai serve agents` (serve.py:299)",
   "module_kind": "auth dependency (FastAPI Depends) shared by the router"
  },
  {
   "where": "fix.diff:463-502 (src/praisonai/praisonai/api/call.py:137-154)",
   "entry_point": "HTTP GET/POST / on the call server (`praisonai call`)",
   "module_kind": "HTTP handler (Twilio webhook)"
  },
  {
   "where": "fix.diff:510-521 (src/praisonai/praisonai/api/call.py:177-181)",
   "entry_point": "WebSocket /media-stream on the call server",
   "module_kind": "WebSocket handler"
  }
 ],
 "O1_entry_points": 7,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "Every published fix site for this protection is in src/praisonai/praisonai/api/. The other changed files in the diff belong to separate bundled advisories (see out_of_scope_notes)."
 },
 "O3_reason_to_dismiss": "`praisonai serve agents` is a separate server with its own optional --api-key middleware and a 127.0.0.1 default bind, so a solver can argue the Call API advisory does not cover it, even though it mounts the same verify_token router and adds unauthenticated /agents routes into the same agent registry.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Two legitimate behaviours sit next to the sink. (1) PRAISONAI_CALL_AUTH=disabled must keep working on a genuine localhost bind (tested at fix.diff:955-973). (2) The Twilio TwiML handler must keep building the wss:// stream URL from request.url.hostname. An over-broad fix that rejects any request based on Host, or removes the opt-out, breaks one of them.",
  "where": "src/praisonai/praisonai/api/call.py:160-165"
 },
 "O6_input_shapes": [
  "bind host values 127.0.0.1, localhost, ::1 (fix.diff:412)",
  "token via Authorization Bearer (src/praisonai/praisonai/api/agent_invoke.py:57-58)",
  "token via Authorization Basic, password or bare value (src/praisonai/praisonai/api/agent_invoke.py:59-68)",
  "token via ?token= query parameter (src/praisonai/praisonai/api/agent_invoke.py:71-72)",
  "PRAISONAI_CALL_AUTH case-insensitive 'disabled' (src/praisonai/praisonai/api/agent_invoke.py:32)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "src/praisonai/praisonai/api/call.py:354-363 (run_server knows the bind address but neither exposes nor exports it; it hard-codes 0.0.0.0) and src/praisonai/praisonai/cli/features/serve.py:225,246 (serve agents bind host). The 2a855c4 check reads request.url instead (fix.diff:420). Latest has run_server export PRAISONAI_CALL_BIND_HOST, and verify_token reads it.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "`praisonai serve agents` mounts the same verify_token router, so PRAISONAI_CALL_AUTH=disabled opens it on any --host. It also exposes unauthenticated POST {path} and POST /agents/{agent_name} into the same agent registry when --api-key is unset, with no non-localhost bind guard.",
   "where": "src/praisonai/praisonai/cli/features/serve.py:294-302",
   "reason_to_dismiss": "It is a different server with its own --api-key option and a 127.0.0.1 default (serve.py:70), so a solver can call it 'not the Call API'.",
   "distance": "different package (cli/features vs api), about 1000-line file",
   "present_in_latest": "no",
   "latest_where": "latest/src/praisonai/praisonai/cli/features/serve.py:320-327"
  },
  {
   "route": "The unauthenticated n8n alias POST /agents/{agent_name} invokes registry agents directly with no verify_token and no api-key unless --api-key is set.",
   "where": "src/praisonai/praisonai/cli/features/serve.py:376-400",
   "reason_to_dismiss": "Labelled an 'n8n compatibility endpoint' and protected by the optional serve --api-key middleware (serve.py:441), not by the Call API token.",
   "distance": "different package from the landing point",
   "present_in_latest": "no",
   "latest_where": "latest/src/praisonai/praisonai/cli/features/serve.py:479-485"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/praisonai/praisonai/cli/features/serve.py:441",
   "sibling": "Add a PRAISONAI_SERVE_AUTH=disabled opt-out to _install_api_key_middleware that is gated on request.url.hostname being localhost.",
   "why_realistic": "It mirrors the call API's opt-out exactly. Upstream itself first wrote the Host-header gate in 2a855c4, so a maintainer copying that pattern is plausible."
  },
  {
   "where": "src/praisonai/praisonai/api/call.py:137-154",
   "sibling": "Let the TwiML / handler honour PRAISONAI_CALL_AUTH=disabled with the same localhost-by-Host check.",
   "why_realistic": "The handler already reads request.url.hostname at call.py:160, and the two auth blocks are near-duplicates of verify_token."
  }
 ],
 "O9_family": "authentication bypass: locality decision trusted from a client-controlled Host header (CWE-287/306/346)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "pip/uv, pyproject in src/praisonai and src/praisonai-agents; pytest + pytest-asyncio",
  "services": [],
  "offline_after_build": true,
  "project_tests": "src/praisonai/tests/unit/test_call_server_auth.py (calls verify_token directly with a fake request), src/praisonai/tests/test_n8n_agent_invoke.py; call.py imports twilio, pyngrok, websockets at module level, so the [call] extras are needed to import it"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/praisonai/praisonai/api/agent_invoke.py, src/praisonai/praisonai/api/call.py (advisory-relevant); the diff also touches 12 other source files for unrelated bundled advisories",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Gate the PRAISONAI_CALL_AUTH=disabled branch on request.url.hostname / Host header being localhost, which is exactly what upstream's first fix 2a855c4 did and which the advisory says is spoofable."
 },
 "out_of_scope_notes": [
  "fix.diff bundles at least 6 other advisories in one commit: SearxNG SSRF (praisonaiagents/tools/searxng_tools.py, web_search.py, url_safety.py), platform JWT default secret (praisonai_platform/services/auth_service.py, jwt_secret.py), recipe tool-policy and workflow approve gating (recipe/core.py, cli/features/recipe.py, workflows/workflows.py), A2U bind guard (cli/features/serve.py:cmd_a2u), sandlock fallback tagging (sandbox/sandlock.py), multiedit path traversal (tools/multiedit.py).",
  "The supplied fix.diff contains only 2a855c4. Its test labels the Call API change 'GHSA-8ccj call auth' (fix.diff:931), not GHSA-2gpf. The Host-header fix for GHSA-2gpf is presumably 846568c, which is not in fix.diff.",
  "call.py handle_incoming_call and media-stream compare tokens with != (not constant time) at the pinned commit (call.py:153,179); latest uses hmac/_tokens_match."
 ],
 "unverified": [
  "MISMATCH: the pinned tree (parent of 2a855c4) has no localhost check at all (agent_invoke.py:42-43), so the advisory's 'spoofed Host header' mechanism does not exist at the pin. It is introduced by fix.diff:419-436. A faithful GHSA-2gpf task probably needs to be pinned at 2a855c4 and scored against 846568c, whose diff was not provided and was not read.",
  "Contents of 846568c not inspected. The latest-code shape (env PRAISONAI_CALL_BIND_HOST, latest/src/praisonai/praisonai/api/agent_invoke.py:53-67; run_server exporting it, latest/src/praisonai/praisonai/api/call.py:722) is inferred to be its result.",
  "Repo size in MB not measured (about 11.5k files incl. a TypeScript SDK; likely well above 5 MB and below 1.5 GB).",
  "Recall risk estimated from the 18 sibling advisories on this repo. Write-up coverage was not checked (no network).",
  "Whether verify_token's Host-based check is reached via proxied deployments (X-Forwarded-Host / ProxyHeadersMiddleware) was not checked."
 ]
}
  ```
- Published fix sites:   - fix.diff:410-452 (src/praisonai/praisonai/api/agent_invoke.py:31-51) — entry point: HTTP POST /api/v1/agents/{agent_id}/invoke, GET /api/v1/agents, POST /api/v1/agents/{agent_id}/register, DELETE /api/v1/agents/{agent_id}, GET /api/v1/agents/{agent_id} (all Depends(verify_token)), mounted by `praisonai call` (call.py:61) and `praisonai serve agents` (serve.py:299) [auth dependency (FastAPI Depends) shared by the router]
  - fix.diff:463-502 (src/praisonai/praisonai/api/call.py:137-154) — entry point: HTTP GET/POST / on the call server (`praisonai call`) [HTTP handler (Twilio webhook)]
  - fix.diff:510-521 (src/praisonai/praisonai/api/call.py:177-181) — entry point: WebSocket /media-stream on the call server [WebSocket handler]
- Uncovered routes to confirm (pattern B):   - src/praisonai/praisonai/cli/features/serve.py:294-302 — `praisonai serve agents` mounts the same verify_token router, so PRAISONAI_CALL_AUTH=disabled opens it on any --host. It also exposes unauthenticated POST {path} and POST /agents/{agent_name} into the same agent registry when --api-key is unset, with no non-localhost bind guard. (reason to dismiss: It is a different server with its own --api-key option and a 127.0.0.1 default (serve.py:70), so a solver can call it 'not the Call API'.; still in latest: no)
  - src/praisonai/praisonai/cli/features/serve.py:376-400 — The unauthenticated n8n alias POST /agents/{agent_name} invokes registry agents directly with no verify_token and no api-key unless --api-key is set. (reason to dismiss: Labelled an 'n8n compatibility endpoint' and protected by the optional serve --api-key middleware (serve.py:441), not by the Call API token.; still in latest: no)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
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
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

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

## Environment (`tasks/praisonai-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/praisonai-mm/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/praisonai-mm/tests/`)
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
- **Wrong-fix patches** go in `build/praisonai-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/praisonai-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/praisonai-mm/manifest.json`:**
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

**Also in `build/praisonai-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py praisonai-mm --only static
python3 -I builder/gate.py praisonai-mm --only nop
python3 -I builder/gate.py praisonai-mm --only oracle
python3 -I builder/gate.py praisonai-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/praisonai-mm/`;
  - edit only `tasks/praisonai-mm/`, `build/praisonai-mm/` and, for pattern B, the register;
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
