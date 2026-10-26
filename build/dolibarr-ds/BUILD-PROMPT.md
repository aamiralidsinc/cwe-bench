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

Project root: `/home/mara/cwe-bench`. Task: `dolibarr-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-7FG5-VC77-69FP", "CVE-2026-10215"]; dolibarr/dolibarr; improper authorization: missing hierarchy/ownership (IDOR-style) check in REST API
- Pinned (vulnerable) commit: 3566f80aa88fd26b295ad8762d02327915ee79ec. Published fix: ee93b6f2f9dd0f6aeefe9d718ab3ab0a44326b73.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "32869",
 "advisory_ids": [
  "GHSA-7FG5-VC77-69FP",
  "CVE-2026-10215"
 ],
 "repo": "dolibarr/dolibarr",
 "pinned_commit": "3566f80aa88fd26b295ad8762d02327915ee79ec",
 "fix_commits": [
  "ee93b6f2f9dd0f6aeefe9d718ab3ab0a44326b73"
 ],
 "trust_decision": {
  "summary": "Whether an API user with plain read/write/approve rights may act on a leave request or expense report of a user outside their hierarchy (not self or subordinate, no readall). checkUserAccessToObject decides this, but runs the hierarchy test only when given the full object. The REST APIs passed only the ID, so the test was skipped.",
  "evidence": [
   "htdocs/core/lib/security.lib.php:1037",
   "htdocs/core/lib/security.lib.php:1249-1267",
   "htdocs/api/class/api.class.php:393-409",
   "htdocs/holiday/class/api_holidays.class.php:87",
   "fix.diff:175-176"
  ]
 },
 "landing_point": {
  "where": "htdocs/holiday/class/api_holidays.class.php:87",
  "why": "The summary names the Leave Request REST API. Holidays::get is the first object-level check in that class."
 },
 "fix_sites": [
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:87",
   "entry_point": "GET /holidays/{id} (Holidays::get)",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:268",
   "entry_point": "PUT /holidays/{id} (Holidays::put)",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:321",
   "entry_point": "DELETE /holidays/{id} (Holidays::delete)",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:366",
   "entry_point": "Holidays::validate REST action",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:412",
   "entry_point": "Holidays::approve REST action",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:458",
   "entry_point": "Holidays::cancel REST action",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:505",
   "entry_point": "Holidays::refuse REST action",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:555",
   "entry_point": "Holidays::reopen REST action",
   "module_kind": "REST API handler, holiday module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:109",
   "entry_point": "GET /expensereports/{id} (ExpenseReports::get)",
   "module_kind": "REST API handler, expensereport module (not named in advisory)"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:287",
   "entry_point": "GET /expensereports/{id}/lines",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:327",
   "entry_point": "POST /expensereports/{id}/line",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:389",
   "entry_point": "PUT /expensereports/{id}/lines/{lineid}",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:457",
   "entry_point": "DELETE /expensereports/{id}/lines/{lineid}",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:515",
   "entry_point": "PUT /expensereports/{id}",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:568",
   "entry_point": "DELETE /expensereports/{id}",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:609",
   "entry_point": "POST /expensereports/{id}/settodraft",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:653",
   "entry_point": "POST /expensereports/{id}/validate",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:698",
   "entry_point": "POST /expensereports/{id}/approve",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:744",
   "entry_point": "POST /expensereports/{id}/deny",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:790",
   "entry_point": "POST /expensereports/{id}/setpaid",
   "module_kind": "REST API handler, expensereport module"
  },
  {
   "where": "htdocs/expensereport/class/api_expensereports.class.php:832",
   "entry_point": "POST /expensereports/{id}/cancel",
   "module_kind": "REST API handler, expensereport module"
  }
 ],
 "O1_entry_points": 21,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "htdocs/expensereport/class/api_expensereports.class.php:109 (13 sites). This is a second module's REST API under the same hierarchy rule (htdocs/core/lib/security.lib.php:1260-1266). The advisory names only the Leave Request API."
 },
 "O3_reason_to_dismiss": "The advisory is about the Leave Request API, so a solver could treat expense reports as a separate module with its own advisory. Also, ExpenseReports::index needs only 'lire', not 'readall' as Holidays::index does, which a solver could read as intended for list views.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The leave validator (fk_validator) must keep access to a leave whose owner is outside their hierarchy, and readall holders must keep access to all records. A fix that checks only owner-in-childids, or that requires readall, breaks approve/refuse by the assigned validator and self-service for normal employees.",
  "where": "htdocs/core/lib/security.lib.php:1255-1257"
 },
 "O6_input_shapes": [
  "Full object passed instead of a numeric ID (the hierarchy branch requires is_object, htdocs/core/lib/security.lib.php:1251)",
  "Comma-separated ID list accepted by checkUserAccessToObject (htdocs/core/lib/security.lib.php:981), but this ID-only path still skips the hierarchy check after the fix"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Hierarchy data comes from User::getAllChildIds, called directly by the check at htdocs/core/lib/security.lib.php:1252",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /expensereports list returns every expense report in the entity to any user with 'lire', with no hierarchy filter. Holidays::index requires readall.",
   "where": "htdocs/expensereport/class/api_expensereports.class.php:138-154",
   "reason_to_dismiss": "List endpoint, not a per-object check. The fix pattern (pass the object) does not apply, and the user_ids filter looks like a deliberate feature.",
   "distance": "same file as 13 fix sites; needs an SQL filter on childids (a different mechanism)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "POST /expensereports and POST /holidays accept the target-user field (fk_user_author / fk_user) from the request body with no hierarchy check. The web create path enforces one.",
   "where": "htdocs/expensereport/class/api_expensereports.class.php:228-257",
   "reason_to_dismiss": "Create has no existing object to check, and the advisory is about access to existing leave requests.",
   "distance": "same files as fix; web counterparts at htdocs/expensereport/card.php:286-298 and htdocs/holiday/card.php:211-220",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Expense report payment endpoints (GET /payments, GET /payments/{pid}, POST {id}/payments, PUT {id}/payments) check only the module right and never check the parent report's hierarchy.",
   "where": "htdocs/expensereport/class/api_expensereports.class.php:865-1017",
   "reason_to_dismiss": "Payments are a separate object (PaymentExpenseReport) and an accounting/treasury feature, not the expense report itself.",
   "distance": "same file, different object class",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Documents API listing by element for modulepart expensereport/holiday checks only the module right, with no object or hierarchy check.",
   "where": "htdocs/api/class/api_documents.class.php:655-682",
   "reason_to_dismiss": "Generic documents API shared by all modules. It returns file metadata, not the leave record, and other modules there have no object-level check either.",
   "distance": "another package (htdocs/api), 1 file away from landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Web AJAX mileage computation calls restrictedArea with an ID only, so the hierarchy test is skipped for any fk_expense.",
   "where": "htdocs/expensereport/ajax/ajaxik.php:64",
   "reason_to_dismiss": "Web UI helper, not the REST API, and it returns only a computed mileage amount.",
   "distance": "another directory (expensereport/ajax)",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:114-120",
   "sibling": "Relax index() from readall to read plus a user_ids filter (the TODO at line 116 asks for this) without checking that every ID is in childids.",
   "why_realistic": "The maintainer's own TODO describes exactly this relaxation. Implementing it naively reintroduces the hierarchy gap through a filter parameter (how-type: identity in a list param)."
  },
  {
   "where": "htdocs/holiday/class/api_holidays.class.php:271-289",
   "sibling": "put() lets fk_validator be reassigned after the check. Since the check grants access when fk_validator is in childids (htdocs/core/lib/security.lib.php:1256), a planted update of fk_user would be a change-after-check.",
   "why_realistic": "The generic field-copy loop already assigns any property, and Holiday::update persists fk_validator (htdocs/holiday/class/holiday.class.php:1064)."
  }
 ],
 "O9_family": "improper authorization: missing hierarchy/ownership (IDOR-style) check in REST API",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "PHP 8.x + composer-less vendored libs; PHPUnit for tests",
  "services": [
   "MySQL/MariaDB or PostgreSQL",
   "web server for REST API (Restler)"
  ],
  "offline_after_build": true,
  "project_tests": "test/phpunit/HolidayTest.php, test/phpunit/ExpenseReportTest.php, test/phpunit/SecurityTest.php (object-level; no REST hierarchy tests seen)"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "htdocs/holiday/class/api_holidays.class.php, htdocs/expensereport/class/api_expensereports.class.php, htdocs/api/class/api.class.php (docblock only)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Pass $this->holiday instead of ->id in api_holidays only, or require readall on every holiday endpoint, which breaks validators and self-service."
 },
 "out_of_scope_notes": [
  "dol_check_secure_access_document calls checkUserAccessToObject with global $user instead of $fuser (htdocs/core/lib/files.lib.php:3130, 3142). Not pursued.",
  "The fix commit message cites GHSA-qjj8-wpvx-p54j, not GHSA-7FG5-VC77-69FP (fix.diff:2)."
 ],
 "unverified": [
  "Exact @url routes for holiday actions (validate/approve/cancel/refuse/reopen) were inferred from method names, not read from annotations.",
  "repo_mb not measured.",
  "Whether Restler exposes the ExpenseReport payment and documents endpoints exactly as annotated was not run.",
  "O2 kind: the expense-report API is a parallel module under the same rule, not strictly a second implementation of the leave API. second_implementation is the closest enum value.",
  "O4 counts: landing file, api_expensereports.class.php, and api_documents.class.php / security.lib.php as the farthest. Approximate.",
  "present_in_latest is unknown for all O8 routes (no latest release given)."
 ]
}
  ```
- Published fix sites:   - htdocs/holiday/class/api_holidays.class.php:87 — entry point: GET /holidays/{id} (Holidays::get) [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:268 — entry point: PUT /holidays/{id} (Holidays::put) [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:321 — entry point: DELETE /holidays/{id} (Holidays::delete) [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:366 — entry point: Holidays::validate REST action [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:412 — entry point: Holidays::approve REST action [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:458 — entry point: Holidays::cancel REST action [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:505 — entry point: Holidays::refuse REST action [REST API handler, holiday module]
  - htdocs/holiday/class/api_holidays.class.php:555 — entry point: Holidays::reopen REST action [REST API handler, holiday module]
  - htdocs/expensereport/class/api_expensereports.class.php:109 — entry point: GET /expensereports/{id} (ExpenseReports::get) [REST API handler, expensereport module (not named in advisory)]
  - htdocs/expensereport/class/api_expensereports.class.php:287 — entry point: GET /expensereports/{id}/lines [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:327 — entry point: POST /expensereports/{id}/line [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:389 — entry point: PUT /expensereports/{id}/lines/{lineid} [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:457 — entry point: DELETE /expensereports/{id}/lines/{lineid} [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:515 — entry point: PUT /expensereports/{id} [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:568 — entry point: DELETE /expensereports/{id} [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:609 — entry point: POST /expensereports/{id}/settodraft [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:653 — entry point: POST /expensereports/{id}/validate [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:698 — entry point: POST /expensereports/{id}/approve [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:744 — entry point: POST /expensereports/{id}/deny [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:790 — entry point: POST /expensereports/{id}/setpaid [REST API handler, expensereport module]
  - htdocs/expensereport/class/api_expensereports.class.php:832 — entry point: POST /expensereports/{id}/cancel [REST API handler, expensereport module]
- Uncovered routes to confirm (pattern B):   - htdocs/expensereport/class/api_expensereports.class.php:138-154 — GET /expensereports list returns every expense report in the entity to any user with 'lire', with no hierarchy filter. Holidays::index requires readall. (reason to dismiss: List endpoint, not a per-object check. The fix pattern (pass the object) does not apply, and the user_ids filter looks like a deliberate feature.; still in latest: unknown)
  - htdocs/expensereport/class/api_expensereports.class.php:228-257 — POST /expensereports and POST /holidays accept the target-user field (fk_user_author / fk_user) from the request body with no hierarchy check. The web create path enforces one. (reason to dismiss: Create has no existing object to check, and the advisory is about access to existing leave requests.; still in latest: unknown)
  - htdocs/expensereport/class/api_expensereports.class.php:865-1017 — Expense report payment endpoints (GET /payments, GET /payments/{pid}, POST {id}/payments, PUT {id}/payments) check only the module right and never check the parent report's hierarchy. (reason to dismiss: Payments are a separate object (PaymentExpenseReport) and an accounting/treasury feature, not the expense report itself.; still in latest: unknown)
  - htdocs/api/class/api_documents.class.php:655-682 — Documents API listing by element for modulepart expensereport/holiday checks only the module right, with no object or hierarchy check. (reason to dismiss: Generic documents API shared by all modules. It returns file metadata, not the leave record, and other modules there have no object-level check either.; still in latest: unknown)
  - htdocs/expensereport/ajax/ajaxik.php:64 — Web AJAX mileage computation calls restrictedArea with an ID only, so the hierarchy test is skipped for any fk_expense. (reason to dismiss: Web UI helper, not the REST API, and it returns only a computed mileage amount.; still in latest: unknown)
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

## Environment (`tasks/dolibarr-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/dolibarr-ds/instruction.md`)
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

## Tests (`tasks/dolibarr-ds/tests/`)
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
- **Wrong-fix patches** go in `build/dolibarr-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/dolibarr-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/dolibarr-ds/manifest.json`:**
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

**Also in `build/dolibarr-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py dolibarr-ds --only static
python3 -I builder/gate.py dolibarr-ds --only nop
python3 -I builder/gate.py dolibarr-ds --only oracle
python3 -I builder/gate.py dolibarr-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/dolibarr-ds/`;
  - edit only `tasks/dolibarr-ds/`, `build/dolibarr-ds/` and, for pattern B, the register;
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
