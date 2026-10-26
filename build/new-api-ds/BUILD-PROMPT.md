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

Project root: `/home/mara/cwe-bench`. Task: `new-api-ds`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-6X2C-PHFF-WX57", "CVE-2026-64859", "GO-2026-6240"]; quantumnous/new-api; CWE-200 sensitive credential exposure via over-broad model serialization to lower-privileged admins, with missing role-hierarchy authorization (A01)
- Pinned (vulnerable) commit: parent of 0936e2504655a5cbf7bc3c388f6d3e2bb24916d3 (parent_commit not given in candidate). Published fix: 0936e2504655a5cbf7bc3c388f6d3e2bb24916d3.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "16277",
 "advisory_ids": [
  "GHSA-6X2C-PHFF-WX57",
  "CVE-2026-64859",
  "GO-2026-6240"
 ],
 "repo": "quantumnous/new-api",
 "pinned_commit": "parent of 0936e2504655a5cbf7bc3c388f6d3e2bb24916d3 (parent_commit not given in candidate)",
 "fix_commits": [
  "0936e2504655a5cbf7bc3c388f6d3e2bb24916d3"
 ],
 "trust_decision": {
  "summary": "Which User fields leave the server is decided by the JSON tags on the shared model.User struct. AccessToken (the panel-management bearer credential) is tagged json:\"access_token\", so any admin-only route that serializes a User, including the root user in list/search results, returns it. Separately, the role-hierarchy check (actor must outrank the target, or be root) is enforced per handler and was missing in AdminResetPasskey.",
  "evidence": [
   "model/user.go:39",
   "controller/user.go:236-249",
   "controller/user.go:251-265",
   "middleware/auth.go:54",
   "controller/passkey.go:341-354",
   "fix.diff:232-235",
   "fix.diff:31-35"
  ]
 },
 "landing_point": {
  "where": "controller/user.go:236",
  "why": "The summary names the 'User List API'. GetAllUsers (GET /api/user/, router/api-router.go:127) passes model.GetAllUsers results straight into the page items with no role filtering or field stripping."
 },
 "fix_sites": [
  {
   "where": "model/user.go:39",
   "entry_point": "GET /api/user/ (GetAllUsers), GET /api/user/search (SearchUsers), GET /api/user/:id (GetUser): every route that serializes model.User",
   "module_kind": "data model / serializer tag (model package, not the handler)"
  },
  {
   "where": "controller/passkey.go:341",
   "entry_point": "DELETE /api/user/:id/reset_passkey (AdminResetPasskey), router/api-router.go:139",
   "module_kind": "neighbouring feature handler (passkey); newly added role-hierarchy guard"
  },
  {
   "where": "controller/user.go:279",
   "entry_point": "GET /api/user/:id (GetUser)",
   "module_kind": "handler; refactor to canManageTargetRole only, no change in meaning"
  },
  {
   "where": "controller/user.go:570",
   "entry_point": "PUT /api/user/ (UpdateUser)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "controller/user.go:613",
   "entry_point": "DELETE /api/user/:id/bindings/:binding_type (AdminClearUserBinding)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "controller/user.go:875",
   "entry_point": "POST /api/user/manage (ManageUser)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "controller/custom_oauth.go:504",
   "entry_point": "GET /api/user/:id/oauth/bindings (GetUserOAuthBindingsByAdmin)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "controller/custom_oauth.go:563",
   "entry_point": "DELETE /api/user/:id/oauth/bindings/:provider_id (UnbindCustomOAuthByAdmin)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "controller/twofa.go:523",
   "entry_point": "DELETE /api/user/:id/2fa (AdminDisable2FA)",
   "module_kind": "handler; refactor only, no change in meaning"
  },
  {
   "where": "fix.diff:159-162",
   "entry_point": "logger.LogJson (internal; debug logging)",
   "module_kind": "logging helper; gated on DebugEnabled (log-hygiene hardening)"
  },
  {
   "where": "fix.diff:274-277",
   "entry_point": "relay request path (DoApiRequest), via any relay route",
   "module_kind": "logging; about 25 other files change println to logger.LogDebug (hygiene, not the advisory's protection)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "model/user.go:39 (serializer tag on the shared struct, in package model, two hops from the list handler). Also controller/passkey.go:341 as a neighbouring-feature guard"
 },
 "O3_reason_to_dismiss": "For the Setting blob: 'the advisory is about the access token that grants panel login; webhook/Gotify settings are notification config the admin already manages, not a privilege-escalation credential.' For passkey reset: 'the report is about an information leak in the list API, not about passkey management.'",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "GET /api/user/self/token (GenerateAccessToken) must keep returning the freshly generated token to its owner, and Authorization-header login through ValidateAccessToken must keep working. A fix that nulls or stops persisting AccessToken, or that blocks it at the DB/query layer for every read, breaks both. Admins must also keep seeing the other fields of lower-role users in list/search.",
  "where": "controller/user.go:291-324"
 },
 "O6_input_shapes": [
  "single User object in the response (GetUser, controller/user.go:283-287)",
  "paginated []*User list (GetAllUsers controller/user.go:244-247; SearchUsers controller/user.go:261-263)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "model/user.go:39 (json tag on User.AccessToken). Queries omit only password (model/user.go:214, model/user.go:281, model/user.go:304)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Admin user list/search still serializes User.Setting, a raw JSON string holding webhook_secret and gotify_token, for root and other higher-role users, with no role filtering.",
   "where": "model/user.go:51",
   "reason_to_dismiss": "Notification settings, not a login credential; the advisory names only the access token.",
   "distance": "the secret's fields are defined in dto/user_settings.go:7 and dto/user_settings.go:11; the struct field is in model/user.go; reached via controller/user.go:245 and controller/user.go:262 (3 files, 3 packages)",
   "present_in_latest": "yes",
   "latest_where": "latest/model/user.go:108"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "controller/user.go:397-423",
   "sibling": "GetSelf builds a hand-written response map; adding \"access_token\": user.GetAccessToken() there, or in a similar admin 'user detail' map, would bypass the struct tag.",
   "why_realistic": "The frontend shows the management token in the profile page, so a maintainer might echo it from GetSelf for convenience. A hand-built map ignores json:\"-\"."
  },
  {
   "where": "model/user_cache.go:72-76",
   "sibling": "Caching the full User (rather than UserBase) in Redis and returning the cached object from an admin endpoint.",
   "why_realistic": "A performance refactor could swap ToBaseUser() for the full struct. A cache serializer with its own field naming (HSet via reflection, not encoding/json) would ignore the json tag."
  },
  {
   "where": "controller/user.go:236-249",
   "sibling": "An admin CSV/JSON 'export users' endpoint that reuses model.GetAllUsers but marshals through a separate DTO copying all fields.",
   "why_realistic": "A user export is a common admin feature request. A copied DTO would carry AccessToken over without the tag."
  }
 ],
 "O9_family": "CWE-200 sensitive credential exposure via over-broad model serialization to lower-privileged admins, with missing role-hierarchy authorization (A01)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.25.1 (go.mod:4); web frontend not needed for API tests",
  "services": [
   "none required: SQLite via github.com/glebarez/sqlite (go.mod:21); Redis optional"
  ],
  "offline_after_build": true,
  "project_tests": "No controller tests for user/passkey handlers at the pinned commit (controller/*_test.go covers token, topup, channel, model_list only). Tests would need gin httptest plus in-memory SQLite."
 },
 "O11_fix_minutes": 30,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "model/user.go, controller/user.go, controller/passkey.go, controller/custom_oauth.go, controller/twofa.go, logger/logger.go, plus about 27 logging-only files (controller/task_video.go, model/channel*.go, relay/**, service/**)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Strip AccessToken (or hide root rows) inside GetAllUsers only, missing SearchUsers and GetUser, or never fixing the shared struct tag."
 },
 "out_of_scope_notes": [
  "DeleteUser uses 'myRole <= originUser.Role' with no root exception (controller/user.go:775), so root cannot delete another root. Different behaviour, not pursued.",
  "Relay debug logging may print fullRequestURL, which can carry upstream keys in query strings. The fix only reroutes it through logger.LogDebug (fix.diff:274-277). Log exposure is a separate concern."
 ],
 "unverified": [
  "Repo size in MB was not measured (no shell used); tiny_repo/giant_repo not assessed, though the repo is clearly a large multi-package Go service.",
  "Exact pinned commit hash not given in candidate (parent_commit null).",
  "Whether the frontend relies on access_token appearing in the GET /api/user/:id response was not checked (web/ not read).",
  "Pattern A is weak: the single struct-tag change closes every token-leak route at once, and the canManageTargetRole edits keep the same meaning, so only the passkey guard adds real scope. Hidden tests on passkey reset may be judged unfair given a report about the list API."
 ]
}
  ```
- Published fix sites:   - model/user.go:39 — entry point: GET /api/user/ (GetAllUsers), GET /api/user/search (SearchUsers), GET /api/user/:id (GetUser): every route that serializes model.User [data model / serializer tag (model package, not the handler)]
  - controller/passkey.go:341 — entry point: DELETE /api/user/:id/reset_passkey (AdminResetPasskey), router/api-router.go:139 [neighbouring feature handler (passkey); newly added role-hierarchy guard]
  - controller/user.go:279 — entry point: GET /api/user/:id (GetUser) [handler; refactor to canManageTargetRole only, no change in meaning]
  - controller/user.go:570 — entry point: PUT /api/user/ (UpdateUser) [handler; refactor only, no change in meaning]
  - controller/user.go:613 — entry point: DELETE /api/user/:id/bindings/:binding_type (AdminClearUserBinding) [handler; refactor only, no change in meaning]
  - controller/user.go:875 — entry point: POST /api/user/manage (ManageUser) [handler; refactor only, no change in meaning]
  - controller/custom_oauth.go:504 — entry point: GET /api/user/:id/oauth/bindings (GetUserOAuthBindingsByAdmin) [handler; refactor only, no change in meaning]
  - controller/custom_oauth.go:563 — entry point: DELETE /api/user/:id/oauth/bindings/:provider_id (UnbindCustomOAuthByAdmin) [handler; refactor only, no change in meaning]
  - controller/twofa.go:523 — entry point: DELETE /api/user/:id/2fa (AdminDisable2FA) [handler; refactor only, no change in meaning]
  - fix.diff:159-162 — entry point: logger.LogJson (internal; debug logging) [logging helper; gated on DebugEnabled (log-hygiene hardening)]
  - fix.diff:274-277 — entry point: relay request path (DoApiRequest), via any relay route [logging; about 25 other files change println to logger.LogDebug (hygiene, not the advisory's protection)]
- Uncovered routes to confirm (pattern B):   - model/user.go:51 — Admin user list/search still serializes User.Setting, a raw JSON string holding webhook_secret and gotify_token, for root and other higher-role users, with no role filtering. (reason to dismiss: Notification settings, not a login credential; the advisory names only the access token.; still in latest: yes)
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

## Environment (`tasks/new-api-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/new-api-ds/instruction.md`)
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

## Tests (`tasks/new-api-ds/tests/`)
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
- **Wrong-fix patches** go in `build/new-api-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/new-api-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/new-api-ds/manifest.json`:**
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

**Also in `build/new-api-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py new-api-ds --only static
python3 -I builder/gate.py new-api-ds --only nop
python3 -I builder/gate.py new-api-ds --only oracle
python3 -I builder/gate.py new-api-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/new-api-ds/`;
  - edit only `tasks/new-api-ds/`, `build/new-api-ds/` and, for pattern B, the register;
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
