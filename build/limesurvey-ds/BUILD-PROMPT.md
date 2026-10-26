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

Project root: `/home/mara/cwe-bench`. Task: `limesurvey-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-5C37-5J7W-8MH8", "CVE-2026-50635"]; limesurvey/limesurvey; Host header poisoning of security-sensitive links (CWE-640 weak password recovery via untrusted Host)
- Pinned (vulnerable) commit: unknown (parent of ac2a4f1673de7b56e7a342c338f36e8bb077d4b3; parent_commit not given in candidate). Published fix: ac2a4f1673de7b56e7a342c338f36e8bb077d4b3, b394cb64328aa6db95e3304f82c8c9e603e9ceb0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "32177",
 "advisory_ids": [
  "GHSA-5C37-5J7W-8MH8",
  "CVE-2026-50635"
 ],
 "repo": "limesurvey/limesurvey",
 "pinned_commit": "unknown (parent of ac2a4f1673de7b56e7a342c338f36e8bb077d4b3; parent_commit not given in candidate)",
 "fix_commits": [
  "ac2a4f1673de7b56e7a342c338f36e8bb077d4b3",
  "b394cb64328aa6db95e3304f82c8c9e603e9ceb0"
 ],
 "trust_decision": {
  "summary": "Whether the client-supplied Host header may become the host of absolute URLs placed in emails (password reset / account creation / token opt-in/out links). At the pinned commit it is only checked in LSHttpRequest::getHostInfo against an optional, empty-by-default allowedHosts config, and PasswordManagement deliberately bypasses publicurl, so reset links carry the request Host.",
  "evidence": [
   "application/core/LSHttpRequest.php:293-315",
   "vendor/yiisoft/yii/framework/web/CHttpRequest.php:351-352",
   "application/models/services/PasswordManagement.php:167-171",
   "application/core/Traits/LSApplicationTrait.php:47-60"
  ]
 },
 "landing_point": {
  "where": "application/models/services/PasswordManagement.php:168",
  "why": "The summary names password-reset links; sendForgotPasswordEmailLink builds the reset link with Yii::app()->createAbsoluteUrl (Host-derived, publicurl explicitly disabled per the comment at line 167), reached from the unauthenticated forgotpassword action."
 },
 "fix_sites": [
  {
   "where": "application/models/services/PasswordManagement.php:168",
   "entry_point": "HTTP admin/authentication/sa/forgotpassword (unauthenticated, application/controllers/admin/Authentication.php:279-303)",
   "module_kind": "service (models/services)"
  },
  {
   "where": "application/models/services/PasswordManagement.php:44",
   "entry_point": "HTTP usermanagement/applyEdit -> createAdminUser -> sendPasswordLinkViaEmail(EMAIL_TYPE_REGISTRATION) (application/controllers/UserManagementController.php:219, 1590-1591)",
   "module_kind": "service (models/services)"
  },
  {
   "where": "application/models/services/PasswordManagement.php:260-261",
   "entry_point": "HTTP usermanagement/batchSendAndResetLoginData -> sendPasswordLinkViaEmail(EMAIL_TYPE_RESET_PW) (application/controllers/UserManagementController.php:1145, 1173-1174)",
   "module_kind": "service (models/services)"
  },
  {
   "where": "application/models/services/PasswordManagement.php:221-238",
   "entry_point": "same as above (sendAdminMail error handling for the false return)",
   "module_kind": "service (models/services)"
  },
  {
   "where": "application/core/LimeMailer.php:870-884",
   "entry_point": "any token email (invitation/reminder/registration/confirmation) via LimeMailer::getTokenReplacements (application/core/LimeMailer.php:848)",
   "module_kind": "core mailer (second consumer, survey participant side)"
  },
  {
   "where": "application/core/LSHttpRequest.php:306-315",
   "entry_point": "every web request that calls getHostInfo (createAbsoluteUrl etc.)",
   "module_kind": "core request component (lower-level check)"
  },
  {
   "where": "fix.diff:201-341",
   "entry_point": "new public API App()->createValidatedAbsoluteUrl / isHostAllowed / loadAllowedHosts / writeAllowedHosts in application/core/Traits/LSApplicationTrait.php",
   "module_kind": "application trait shared by web and console apps"
  },
  {
   "where": "application/controllers/admin/Authentication.php:174-178",
   "entry_point": "HTTP admin/authentication/sa/login (successful login writes allowed_hosts.php, fix.diff:21-34)",
   "module_kind": "controller (trust-on-first-use bootstrap)"
  },
  {
   "where": "application/core/LSYii_Application.php:162-167",
   "entry_point": "web application config load (fix.diff:111-116 loads allowed_hosts.php)",
   "module_kind": "config loader"
  },
  {
   "where": "application/core/ConsoleApplication.php:73-86",
   "entry_point": "CLI console commands (e.g. token email cron) config load (fix.diff:47-66)",
   "module_kind": "config loader, second implementation"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "application/core/ConsoleApplication.php:73-86 (fix.diff:47-66): the console application has its own config merge that must also load allowed_hosts.php; plus application/core/LimeMailer.php:870-884 (participant token emails, not account reset)"
 },
 "O3_reason_to_dismiss": "The report is about admin password-reset links; participant opt-in/out and survey links in LimeMailer and the CLI config loader look like unrelated survey/console features, and the console has no Host header at all.",
 "O4_distance": {
  "files": 7,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Token emails must still contain working opt-out/opt-in/survey links (the fix falls back to the controller URL rather than dropping them), and installs without any allowed_hosts/publicurl must keep working (isHostAllowed is lenient when the list is empty); a strict 'reject unless allowlisted' or 'always require publicurl' fix breaks default installs and the mantis #19619 case where admin host differs from publicurl.",
  "where": "application/core/LimeMailer.php:870-885; application/models/services/PasswordManagement.php:167; fix.diff:134-137; fix.diff:239-242"
 },
 "O6_input_shapes": [
  "Host with different letter case (fix lowercases both sides, fix.diff:245, 257)",
  "IPv6 bracketed host (brackets stripped, fix.diff:245)",
  "host equal to the publicurl host (implicitly trusted, fix.diff:247-254)",
  "publicurl set vs unset (createPublicUrl uses configured publicurl, fix.diff:206)",
  "getHostInfo throwing CHttpException vs returning a bad host (fix.diff:205-211, 219-223)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "application/core/LSYii_Application.php:160-173 and application/core/ConsoleApplication.php:73-86 (populate config 'allowedHosts' read by application/core/LSHttpRequest.php:308)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Reset/registration email logo URL built with Yii::app()->createAbsoluteUrl (request Host, publicurl bypassed) in the same render array the fix edited",
   "where": "application/models/services/PasswordManagement.php:279",
   "reason_to_dismiss": "It is only an image URL, carries no secret, so it is cosmetic.",
   "distance": "same file and function as the landing point's sibling (getRenderArray)",
   "present_in_latest": "yes",
   "latest_where": "latest/application/models/services/PasswordManagement.php:320"
  },
  {
   "route": "Save-and-return email reload link (scid + participant token) built without the new isHostAllowed check; Host-derived when publicurl is unset",
   "where": "application/libraries/Save.php:224",
   "reason_to_dismiss": "Participant-side 'save for later' feature, not an account password reset; password is masked in the mail.",
   "distance": "different package (libraries) from models/services",
   "present_in_latest": "yes",
   "latest_where": "latest/application/libraries/Save.php:223"
  },
  {
   "route": "Admin data-entry 'save' email reload link built the same way",
   "where": "application/controllers/admin/DataEntry.php:1988",
   "reason_to_dismiss": "Admin-only data entry feature, legacy controller.",
   "distance": "different package (controllers/admin)",
   "present_in_latest": "yes",
   "latest_where": "latest/application/controllers/admin/DataEntry.php:2178"
  },
  {
   "route": "Admin response-notification emails with STATISTICSURL/EDITRESPONSEURL/VIEWRESPONSEURL links, triggered by a participant's submit request",
   "where": "application/helpers/frontend_helper.php:481-490",
   "reason_to_dismiss": "Notification links to admin pages, require login, so no token leaks.",
   "distance": "different package (helpers)",
   "present_in_latest": "yes",
   "latest_where": "latest/application/helpers/frontend_helper.php:482-491"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "application/controllers/RegisterController.php",
   "sibling": "A registration-confirmation path that builds its own survey link with Yii::app()->createAbsoluteUrl instead of LimeMailer token replacements",
   "why_realistic": "PasswordManagement already shows maintainers deliberately using the app-level createAbsoluteUrl to bypass publicurl (comment at application/models/services/PasswordManagement.php:167)."
  },
  {
   "where": "application/controllers/admin/RemoteControl.php:101",
   "sibling": "A RemoteControl API method that triggers a user password reset email via a second helper using App()->createAbsoluteUrl",
   "why_realistic": "RemoteControl already builds absolute URLs with App()->createAbsoluteUrl, and a lower-level API sending account emails is a common addition."
  }
 ],
 "O9_family": "Host header poisoning of security-sensitive links (CWE-640 weak password recovery via untrusted Host)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "PHP 7.4+/8.x with bundled vendor/ (Yii 1.1 at vendor/yiisoft/yii)",
  "services": [
   "MySQL or PostgreSQL database",
   "mail transport (PHPMailer; can be pointed at a local/debug sink)"
  ],
  "offline_after_build": true,
  "project_tests": "No tests/ directory in the pinned copy; the fix adds tests/unit/ValidatedAbsoluteUrlTest.php (fix.diff:453-781) using ls\\tests\\TestBaseClass, which is absent here."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "application/controllers/admin/Authentication.php, application/core/ConsoleApplication.php, application/core/LSHttpRequest.php, application/core/LSYii_Application.php, application/core/LimeMailer.php, application/core/Traits/LSApplicationTrait.php, application/models/services/PasswordManagement.php, application/views/admin/globalsettings/_security.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace Yii::app()->createAbsoluteUrl with createPublicUrl in sendForgotPasswordEmailLink only, leaving registration/batch-reset, token mails and the empty-by-default allowlist untouched."
 },
 "out_of_scope_notes": [
  "application/libraries/Api/Command/V1/SurveyTemplate.php:162-171 issues a server-side curl with the session cookie to a URL built from raw $_SERVER['HTTP_HOST'] (different sink: outbound request).",
  "application/helpers/common_helper.php:3445 builds an SSL redirect URL from raw $_SERVER['HTTP_HOST'] (redirect sink, not email links).",
  "The fix's trust-on-first-use writes the allowlist from getServerName() at the first admin login (fix.diff:22-25), so the first login's host is trusted."
 ],
 "unverified": [
  "pinned_commit hash not provided and no git metadata read; recorded as parent of the first fix commit.",
  "repo_mb not measured (no shell); the tree has well over 19,000 files incl. vendor/, so tiny_repo does not hold; giant_repo not checked.",
  "Pre-existing defence: application/core/LSHttpRequest.php:306-315 already rejects bad hosts when 'allowedHosts' is set in config.php, so hidden tests must target the default (unset) configuration and/or publicurl; j_defence_ineffective=1 reflects the default-off allowlist, not a bypass.",
  "Fairness concern: the published fix adds new public API names (createValidatedAbsoluteUrl, isHostAllowed, writeAllowedHosts) and a new config file plus a login-time bootstrap; behavioural tests must not depend on those names.",
  "Contribution of the second fix commit b394cb64 cannot be separated from the combined fix.diff.",
  "O1 counts forgotpassword, usermanagement/applyEdit, usermanagement/batchSendAndResetLoginData, and token-email sending; the individual token-email callers (admin tokens, register, console) were not enumerated.",
  "O13 recall_risk estimated from the bug class being widely known; advisory write-ups not checked (no network)."
 ]
}
  ```
- Published fix sites:   - application/models/services/PasswordManagement.php:168 — entry point: HTTP admin/authentication/sa/forgotpassword (unauthenticated, application/controllers/admin/Authentication.php:279-303) [service (models/services)]
  - application/models/services/PasswordManagement.php:44 — entry point: HTTP usermanagement/applyEdit -> createAdminUser -> sendPasswordLinkViaEmail(EMAIL_TYPE_REGISTRATION) (application/controllers/UserManagementController.php:219, 1590-1591) [service (models/services)]
  - application/models/services/PasswordManagement.php:260-261 — entry point: HTTP usermanagement/batchSendAndResetLoginData -> sendPasswordLinkViaEmail(EMAIL_TYPE_RESET_PW) (application/controllers/UserManagementController.php:1145, 1173-1174) [service (models/services)]
  - application/models/services/PasswordManagement.php:221-238 — entry point: same as above (sendAdminMail error handling for the false return) [service (models/services)]
  - application/core/LimeMailer.php:870-884 — entry point: any token email (invitation/reminder/registration/confirmation) via LimeMailer::getTokenReplacements (application/core/LimeMailer.php:848) [core mailer (second consumer, survey participant side)]
  - application/core/LSHttpRequest.php:306-315 — entry point: every web request that calls getHostInfo (createAbsoluteUrl etc.) [core request component (lower-level check)]
  - fix.diff:201-341 — entry point: new public API App()->createValidatedAbsoluteUrl / isHostAllowed / loadAllowedHosts / writeAllowedHosts in application/core/Traits/LSApplicationTrait.php [application trait shared by web and console apps]
  - application/controllers/admin/Authentication.php:174-178 — entry point: HTTP admin/authentication/sa/login (successful login writes allowed_hosts.php, fix.diff:21-34) [controller (trust-on-first-use bootstrap)]
  - application/core/LSYii_Application.php:162-167 — entry point: web application config load (fix.diff:111-116 loads allowed_hosts.php) [config loader]
  - application/core/ConsoleApplication.php:73-86 — entry point: CLI console commands (e.g. token email cron) config load (fix.diff:47-66) [config loader, second implementation]
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

## Environment (`tasks/limesurvey-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/limesurvey-ds/instruction.md`)
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

## Tests (`tasks/limesurvey-ds/tests/`)
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
- **Wrong-fix patches** go in `build/limesurvey-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/limesurvey-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/limesurvey-ds/manifest.json`:**
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

**Also in `build/limesurvey-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py limesurvey-ds --only static
python3 -I builder/gate.py limesurvey-ds --only nop
python3 -I builder/gate.py limesurvey-ds --only oracle
python3 -I builder/gate.py limesurvey-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/limesurvey-ds/`;
  - edit only `tasks/limesurvey-ds/`, `build/limesurvey-ds/` and, for pattern B, the register;
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
