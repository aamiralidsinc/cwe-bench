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

Project root: `/home/mara/cwe-bench`. Task: `portainer-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-X626-FCWX-F5PC", "CVE-2026-55761", "GO-2026-6324"]; portainer/portainer; missing authentication for critical function (first-run admin takeover; CWE-287)
- Pinned (vulnerable) commit: parent of 49f19107cf9a3540cbe406c9eb7f24390e1af02b (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/19774/repo). Published fix: 49f19107cf9a3540cbe406c9eb7f24390e1af02b, d2b56efcb4e43c4168bb6688eee9f6bf22867312.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "19774",
 "advisory_ids": [
  "GHSA-X626-FCWX-F5PC",
  "CVE-2026-55761",
  "GO-2026-6324"
 ],
 "repo": "portainer/portainer",
 "pinned_commit": "parent of 49f19107cf9a3540cbe406c9eb7f24390e1af02b (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/19774/repo)",
 "fix_commits": [
  "49f19107cf9a3540cbe406c9eb7f24390e1af02b",
  "d2b56efcb4e43c4168bb6688eee9f6bf22867312"
 ],
 "trust_decision": {
  "summary": "On an uninitialized instance (no administrator user), anyone reaching the public /restore or /users/admin/init route is trusted to restore the DB or create the first admin; the only check is 'no admin exists yet', in each handler.",
  "evidence": [
   "api/http/handler/backup/handler.go:47",
   "api/http/handler/backup/restore.go:31-39",
   "api/http/handler/users/handler.go:79",
   "api/http/handler/users/admin_init.go:44-58",
   "api/adminmonitor/admin_monitor.go:88-95"
  ]
 },
 "landing_point": {
  "where": "api/http/handler/backup/restore.go:31",
  "why": "The advisory summary names the unauthenticated restore endpoint; its handler only checks WasInitialized and then calls RestoreArchive."
 },
 "fix_sites": [
  {
   "where": "api/http/handler/backup/restore.go:31",
   "entry_point": "POST /api/restore (public, multipart)",
   "module_kind": "HTTP handler (backup package)"
  },
  {
   "where": "api/http/handler/users/admin_init.go:44",
   "entry_point": "POST /api/users/admin/init (public, JSON)",
   "module_kind": "HTTP handler (users package)"
  },
  {
   "where": "api/http/handler/backup/handler.go:17-25",
   "entry_point": "POST /api/restore (handler gains SetupToken field)",
   "module_kind": "handler wiring"
  },
  {
   "where": "api/http/handler/users/handler.go:38",
   "entry_point": "POST /api/users/admin/init (handler gains SetupToken field)",
   "module_kind": "handler wiring"
  },
  {
   "where": "api/http/server.go:144",
   "entry_point": "server start, passes token to backup/users/settings handlers",
   "module_kind": "server composition"
  },
  {
   "where": "api/cmd/portainer/main.go:487-511",
   "entry_point": "binary startup: token generated only if no --admin-password and no admin in DB (fix.diff:30-72)",
   "module_kind": "startup / config"
  },
  {
   "where": "api/cli/cli.go:58",
   "entry_point": "CLI flags --no-setup-token / --setup-token (fix.diff:9-10)",
   "module_kind": "CLI config"
  },
  {
   "where": "api/http/handler/settings/settings_public.go:62-67",
   "entry_point": "GET /api/settings/public exposes RequiresSetupToken (fix.diff:278)",
   "module_kind": "HTTP handler (UI hint)"
  },
  {
   "where": "fix.diff:402-455",
   "entry_point": "new package api/http/security/setuptoken (Generate, Validate)",
   "module_kind": "new security helper"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "api/http/handler/users/admin_init.go:44 (route api/http/handler/users/handler.go:79): a second, independent way to become the first admin on an uninitialized instance, in a different package from the reported restore route"
 },
 "O3_reason_to_dismiss": "The public /users/admin/init is the documented first-run setup wizard, it is not the reported restore route, so gating it can be argued to break intended onboarding.",
 "O4_distance": {
  "files": 11,
  "packages": 8,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "First-run wizard must still be able to create the admin and restore a backup with no user existing (with the correct token); --admin-password startup path and --no-setup-token must bypass the gate; restore on an initialized instance must still return 400; /api/settings/public must stay public. Changing /restore to RestrictedAccess or AdminAccess breaks first-run restore entirely.",
  "where": "api/http/handler/backup/restore.go:32-38; api/cmd/portainer/main.go:487-511; api/adminmonitor/admin_monitor.go:108"
 },
 "O6_input_shapes": [
  "X-Setup-Token header missing -> 403 (fix.diff:214-218, 359-367)",
  "X-Setup-Token header with wrong value -> 403, constant-time compare (fix.diff:220-226, 450)",
  "correct token -> passes (fix.diff:228-233, 380-388)",
  "expected token empty (admin already exists at startup, --admin-password given, or --no-setup-token) -> gate disabled (fix.diff:445-447, 64, 35-37)",
  "JSON body (admin init) vs multipart form (restore) on the two routes"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "fix.diff:30-54 and fix.diff:63-72 (token resolved at startup from --setup-token/env or generated, in api/cmd/portainer/main.go); flags at fix.diff:9-10",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "api/http/handler/backup/handler.go:47",
   "sibling": "A second public restore route on the uninitialized instance (e.g. restore from S3 / remote URL) that calls operations.RestoreArchive with only the WasInitialized check.",
   "why_realistic": "Portainer's business edition ships an S3 restore next to the file restore; a maintainer porting it would copy the existing public restore handler, including its access policy."
  },
  {
   "where": "api/http/handler/system/handler.go:61",
   "sibling": "A deprecated alias route (like the existing deprecated public /status alias) that forwards to adminInit or restore.",
   "why_realistic": "The codebase already keeps deprecated public aliases for backward compatibility; an alias for an older admin-init path is in the same style, and a solver could dismiss it as legacy."
  },
  {
   "where": "api/backup/restore.go:26",
   "sibling": "A lower-level restore path (e.g. restore-on-startup from a file flag or a public helper that wraps RestoreArchive) reachable without the handler gate.",
   "why_realistic": "main.go already has DB-restore-related startup code (api/cmd/portainer/main.go:153); a maintainer could add a restore entry that bypasses the HTTP handler."
  }
 ],
 "O9_family": "missing authentication for critical function (first-run admin takeover; CWE-287)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (backend), plus AngularJS/React frontend that is not needed for the tests",
  "toolchain": "go 1.26.2 (go.mod:3)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "api/http/handler/backup/restore_test.go:23, :81 (restore with passwords, rejection when initialized); handler tests use in-memory testhelpers.NewDatastore / datastore.MustNewTestStore, no external services"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "api/cli/cli.go, api/cmd/portainer/main.go, api/http/handler/backup/handler.go, api/http/handler/backup/restore.go, api/http/handler/settings/handler.go, api/http/handler/settings/settings_public.go, api/http/handler/users/admin_init.go, api/http/handler/users/handler.go, api/http/security/setuptoken/setuptoken.go (new), api/http/server.go, api/portainer.go; plus frontend app/portainer/* and generated API files",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Gate only /restore (or wrap it in RestrictedAccess/AdminAccess), leaving /users/admin/init open, or breaking first-run restore because no user exists yet to authenticate."
 },
 "out_of_scope_notes": [
  "The fix diff also changes unrelated swagger/validate tags on portainer.User (fix.diff:557-593) and the generated TS types; these are not part of the protection.",
  "POST /endpoints/global-key is public but only looks up an existing endpoint by Edge ID (api/http/handler/endpoints/endpoint_create_global_key.go:23-37); it is not a route into the admin/restore sink."
 ],
 "unverified": [
  "pinned_commit hash: parent_commit is null in the candidate; the tree was taken as given and its hash was not read.",
  "repo_mb: not measured (no shell size check); the repo is large (Go backend plus frontend), but the tiny_repo/giant_repo flags cannot be confirmed either way.",
  "O2 kind 'second_implementation' is the closest enum value: admin_init is a separate route into the same 'become first admin' sink, not a copy of the restore code.",
  "Fairness concern (no listed red flag fits): the fix adds a new interface (X-Setup-Token header, Handler.SetupToken fields, --setup-token/--no-setup-token flags, token logged at startup). Hidden tests that use these names (fix.diff:212, 222, 350) need the report to specify them, or the tests must be rewritten against behaviour only.",
  "Other public routes (auth/authenticate, OAuth validate) were judged unable to create an admin on an uninitialized instance because internal auth needs an existing user and OAuth/LDAP need admin-configured settings; this was not traced line by line.",
  "O13 recall risk: published 2026-08-28, after the assistant knowledge cutoff; write-up coverage was estimated from project popularity, not checked.",
  "present_in_latest: both fixed handlers carry setuptoken.Validate in latest (latest/api/http/handler/backup/restore.go:35, latest/api/http/handler/users/admin_init.go:48); there are no O8 routes to report."
 ]
}
  ```
- Published fix sites:   - api/http/handler/backup/restore.go:31 — entry point: POST /api/restore (public, multipart) [HTTP handler (backup package)]
  - api/http/handler/users/admin_init.go:44 — entry point: POST /api/users/admin/init (public, JSON) [HTTP handler (users package)]
  - api/http/handler/backup/handler.go:17-25 — entry point: POST /api/restore (handler gains SetupToken field) [handler wiring]
  - api/http/handler/users/handler.go:38 — entry point: POST /api/users/admin/init (handler gains SetupToken field) [handler wiring]
  - api/http/server.go:144 — entry point: server start, passes token to backup/users/settings handlers [server composition]
  - api/cmd/portainer/main.go:487-511 — entry point: binary startup: token generated only if no --admin-password and no admin in DB (fix.diff:30-72) [startup / config]
  - api/cli/cli.go:58 — entry point: CLI flags --no-setup-token / --setup-token (fix.diff:9-10) [CLI config]
  - api/http/handler/settings/settings_public.go:62-67 — entry point: GET /api/settings/public exposes RequiresSetupToken (fix.diff:278) [HTTP handler (UI hint)]
  - fix.diff:402-455 — entry point: new package api/http/security/setuptoken (Generate, Validate) [new security helper]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/portainer-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/portainer-ds/instruction.md`)
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

## Tests (`tasks/portainer-ds/tests/`)
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
- **Wrong-fix patches** go in `build/portainer-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/portainer-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/portainer-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/portainer-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py portainer-ds --only static
python3 -I builder/gate.py portainer-ds --only nop
python3 -I builder/gate.py portainer-ds --only oracle
python3 -I builder/gate.py portainer-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/portainer-ds/`;
  - edit only `tasks/portainer-ds/`, `build/portainer-ds/` and, for pattern B, the register;
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
