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

Project root: `/home/mara/cwe-bench`. Task: `open-webui-mm`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-3PF7-Q2G3-WJ28", "CVE-2026-87997", "PYSEC-2026-4118"]; open-webui/open-webui; Broken access control / IDOR: missing authorization on a client-supplied foreign key (folder_id) when persisting a chat (CWE-639, CWE-862)
- Pinned (vulnerable) commit: parent of d9e23b90c100d19b00270aea3cde0501d2354a6c (parent_commit not given in candidate). Published fix: d9e23b90c100d19b00270aea3cde0501d2354a6c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "509",
 "advisory_ids": [
  "GHSA-3PF7-Q2G3-WJ28",
  "CVE-2026-87997",
  "PYSEC-2026-4118"
 ],
 "repo": "open-webui/open-webui",
 "pinned_commit": "parent of d9e23b90c100d19b00270aea3cde0501d2354a6c (parent_commit not given in candidate)",
 "fix_commits": [
  "d9e23b90c100d19b00270aea3cde0501d2354a6c"
 ],
 "trust_decision": {
  "summary": "Whether the caller may place a chat row in a given folder (owner, or a direct or inherited 'write' access grant on the folder). This is decided in each chat-writing route before the folder_id is persisted. The chat-completion new-chat path persisted a client-supplied folder_id with no check.",
  "evidence": [
   "backend/open_webui/main.py:1202",
   "backend/open_webui/main.py:1306-1329",
   "backend/open_webui/routers/chats.py:761-769",
   "backend/open_webui/routers/chats.py:2129-2137",
   "backend/open_webui/utils/access_control/folders.py:6-24"
  ]
 },
 "landing_point": {
  "where": "backend/open_webui/main.py:1273-1329",
  "why": "The summary says 'via chat completions'. In chat_completion (POST /api/chat/completions), the is_new_chat branch calls Chats.insert_new_chat with folder_id=metadata['folder_id'] taken straight from the request body."
 },
 "fix_sites": [
  {
   "where": "backend/open_webui/main.py:1273-1274 (fix.diff:17-23)",
   "entry_point": "POST /api/chat/completions, POST /api/v1/chat/completions (and POST Anthropic-compatible messages endpoint via main.py:1950, which calls chat_completion)",
   "module_kind": "HTTP handler (app-level route in main.py)"
  },
  {
   "where": "backend/open_webui/routers/chats.py:761-769 (fix.diff:45-63)",
   "entry_point": "POST /api/v1/chats/new",
   "module_kind": "HTTP router; refactor only, the check was already present"
  },
  {
   "where": "backend/open_webui/routers/chats.py:2129-2137 (fix.diff:71-87)",
   "entry_point": "POST /api/v1/chats/{id}/folder",
   "module_kind": "HTTP router; refactor only, the check was already present"
  },
  {
   "where": "backend/open_webui/utils/access_control/folders.py:6 (fix.diff:99-115)",
   "entry_point": "internal helper has_folder_write_access added; used by the three sites above",
   "module_kind": "access-control helper"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "The only behavioural change is in main.py chat_completion. The chats.py and folders.py hunks consolidate an existing check into a helper (fix.diff:45-63, fix.diff:71-87, fix.diff:110-115)."
 },
 "O3_reason_to_dismiss": "Fork route: the source chat already belongs to the caller and already sits in that folder, so its folder_id was validated when it got there, and copying it looks harmless. This ignores grants revoked or downgraded to read since then.",
 "O4_distance": {
  "files": 1,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "These must keep working: folder_id=None (no folder), the caller's own folders, and shared folders where the caller holds a write grant directly or inherited from an ancestor. A read-only grantee must still be able to chat with folder system prompt and knowledge applied through the read check. An owner-only fix (get_folder_by_id_and_user_id) breaks shared-folder write collaboration. Requiring the folder for temporary or non-saved chats breaks the middleware fallback.",
  "where": "backend/open_webui/utils/access_control/folders.py:8-24; backend/open_webui/utils/middleware.py:2433-2444; backend/open_webui/routers/folders.py:552-561"
 },
 "O6_input_shapes": [
  "folder_id is None: allowed (fix.diff:19)",
  "folder_id of an existing folder owned by the caller",
  "folder_id of a foreign folder with a direct or ancestor-inherited write grant",
  "folder_id that does not exist or is not a UUID: rejected with 404 (fix.diff:112-114)",
  "folder_id of a foreign folder with read-only or no grant: rejected with 404"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "The folder_id is taken directly from the request body at backend/open_webui/main.py:1202; no schema, serializer or cache produces it.",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "Fork copies the source chat's folder_id into a new chat row without re-checking the caller's current write access to that folder, so a revoked or read-only grantee can still add chats to a shared folder.",
   "where": "backend/open_webui/routers/chats.py:1739-1745",
   "reason_to_dismiss": "The source chat is the caller's own and already in that folder, so the folder_id looks pre-validated; fork is a neighbouring feature, not 'chat completions'.",
   "distance": "Different file (routers/chats.py, POST /api/v1/chats/{id}/fork at routers/chats.py:1675) from the landing point main.py; same package.",
   "present_in_latest": "no",
   "latest_where": "latest/backend/open_webui/routers/chats.py:1856-1859"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "backend/open_webui/models/chats.py:617-627",
   "sibling": "import_chats could validate folder_ids with get_folder_by_id only (existence) instead of ownership, admitting foreign folders through POST /api/v1/chats/import.",
   "why_realistic": "The comment says the check is for 'dangling' references, so a maintainer could have written an existence-only check. Upstream later widened this to has_folder_write_access (latest/backend/open_webui/models/chats.py:749-755)."
  },
  {
   "where": "backend/open_webui/routers/chats.py:1785-1794",
   "sibling": "Clone and clone-shared pass the source chat's folder_id via import_chats; a variant that accepts a folder_id from a clone form or skips import validation would reach the same sink.",
   "why_realistic": "The clone form already accepts optional overrides (title, routers/chats.py:1667-1668), so a 'clone into folder' option is a natural feature."
  },
  {
   "where": "backend/open_webui/utils/automations.py:452-466",
   "sibling": "The automation runner re-validates folder ownership at run time; a sibling where the API stores a folder_id it never re-checks (e.g. a run-now or duplicate-automation route) would land chats in a foreign folder.",
   "why_realistic": "The run-time path and the API-time check (routers/automations.py:96-104, tools/builtin.py:3553-3561) are separate copies of the same check."
  }
 ],
 "O9_family": "Broken access control / IDOR: missing authorization on a client-supplied foreign key (folder_id) when persisting a chat (CWE-639, CWE-862)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (FastAPI, async SQLAlchemy) backend; Svelte frontend not needed",
  "toolchain": "Python 3.11+ with pip, backend/requirements.txt (requirements-min.txt also present)",
  "services": [
   "SQLite (default; no external DB needed)",
   "Redis optional (has_active_tasks uses app.state.redis)"
  ],
  "offline_after_build": null,
  "project_tests": "No test_*.py files found in the pinned tree, and the fix diff adds no tests. Hidden tests would need to be written from scratch against the HTTP routes or the helper."
 },
 "O11_fix_minutes": 25,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "backend/open_webui/main.py, backend/open_webui/routers/chats.py, backend/open_webui/utils/access_control/folders.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Check only that the folder is owned by the caller (get_folder_by_id_and_user_id) in chat_completion, breaking shared-folder write grants, and leave the fork route untouched."
 },
 "out_of_scope_notes": [
  "Anthropic-compatible endpoint (main.py:1950) forwards to chat_completion; whether admin-configured passthrough_params can carry parent_id/folder_id was not checked (utils/anthropic.py:381-394).",
  "Folder chat listing returns all users' chats in a folder to any reader (routers/folders.py:565-574); this is where injected chats become visible."
 ],
 "unverified": [
  "pinned_commit hash not given; taken as the parent of the fix commit.",
  "Repo size in MB not measured (no shell); Open WebUI is a large monorepo, so tiny_repo and giant_repo were not assessed.",
  "offline_after_build not verified; the default SQLite setup suggests yes, but model backends are needed for full completions (the folder check happens before any model call, main.py:1273-1306).",
  "Whether a test suite exists outside backend/ (e.g. cypress) was not checked.",
  "O1 counts the two decorators on chat_completion as two entry points; the Anthropic endpoint reaches it only if parent_id/folder_id survive payload conversion (unknown)."
 ]
}
  ```
- Published fix sites:   - backend/open_webui/main.py:1273-1274 (fix.diff:17-23) — entry point: POST /api/chat/completions, POST /api/v1/chat/completions (and POST Anthropic-compatible messages endpoint via main.py:1950, which calls chat_completion) [HTTP handler (app-level route in main.py)]
  - backend/open_webui/routers/chats.py:761-769 (fix.diff:45-63) — entry point: POST /api/v1/chats/new [HTTP router; refactor only, the check was already present]
  - backend/open_webui/routers/chats.py:2129-2137 (fix.diff:71-87) — entry point: POST /api/v1/chats/{id}/folder [HTTP router; refactor only, the check was already present]
  - backend/open_webui/utils/access_control/folders.py:6 (fix.diff:99-115) — entry point: internal helper has_folder_write_access added; used by the three sites above [access-control helper]
- Uncovered routes to confirm (pattern B):   - backend/open_webui/routers/chats.py:1739-1745 — Fork copies the source chat's folder_id into a new chat row without re-checking the caller's current write access to that folder, so a revoked or read-only grantee can still add chats to a shared folder. (reason to dismiss: The source chat is the caller's own and already in that folder, so the folder_id looks pre-validated; fork is a neighbouring feature, not 'chat completions'.; still in latest: no)
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

## Environment (`tasks/open-webui-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/open-webui-mm/instruction.md`)
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

## Tests (`tasks/open-webui-mm/tests/`)
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
- **Wrong-fix patches** go in `build/open-webui-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/open-webui-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/open-webui-mm/manifest.json`:**
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

**Also in `build/open-webui-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py open-webui-mm --only static
python3 -I builder/gate.py open-webui-mm --only nop
python3 -I builder/gate.py open-webui-mm --only oracle
python3 -I builder/gate.py open-webui-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/open-webui-mm/`;
  - edit only `tasks/open-webui-mm/`, `build/open-webui-mm/` and, for pattern B, the register;
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
