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

Project root: `/home/mara/cwe-bench`. Task: `mantisbt-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-3V2J-6FW9-F57C", "CVE-2026-52882"]; mantisbt/mantisbt; Broken access control / authorization bypass through user-controlled key (CWE-639, CWE-863): a role-restricted field is assignable without any level check
- Pinned (vulnerable) commit: 78c0af63d1fe0118004744cab21ca3bf2cea0f5c. Published fix: 17072d4c322c85f7135ebec3417a6d90b525d12f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "31647",
 "advisory_ids": [
  "GHSA-3V2J-6FW9-F57C",
  "CVE-2026-52882"
 ],
 "repo": "mantisbt/mantisbt",
 "pinned_commit": "78c0af63d1fe0118004744cab21ca3bf2cea0f5c",
 "fix_commits": [
  "17072d4c322c85f7135ebec3417a6d90b525d12f"
 ],
 "trust_decision": {
  "summary": "Only a user holding report_issues_for_unreleased_versions_threshold (DEVELOPER) may assign an issue's product version to a version whose released flag is false; the decision belongs at every handler that writes BugData::version (api/soap/mc_issue_api.php:1159, core/commands/IssueAddCommand.php:278, bug_update.php:148, bug_actiongroup.php:260), yet at the pinned commit only the two HTML dropdowns filter the list and no server-side handler consults the version's released flag.",
  "evidence": [
   "config_defaults_inc.php:3604-3609",
   "api/soap/mc_issue_api.php:1155-1163",
   "core/commands/IssueAddCommand.php:278-291",
   "bug_update_page.php:146-151",
   "bug_report_page.php:460-465",
   "core/version_api.php:661-680",
   "api/soap/mc_api.php:888-925"
  ]
 },
 "landing_point": {
  "where": "api/soap/mc_issue_api.php:1159",
  "why": "The summary names the REST and SOAP issue update; both transports end in mc_issue_update, whose unconditional '$t_bug_data->version = $fn_set_version_field( $t_version_id )' (1159) and '$t_bug_data->fixed_in_version' (1160) write whatever version id the payload named, with no access-level or released-status check."
 },
 "fix_sites": [
  {
   "where": "api/soap/mc_issue_api.php:1041-1043,1159-1163",
   "entry_point": "REST PATCH /issues/{id} (api/rest/restcore/issues_rest.php:407-439) and SOAP mc_issue_update (api/soap/mc_issue_api.php:971)",
   "module_kind": "SOAP/REST API implementation layer"
  },
  {
   "where": "core/commands/IssueAddCommand.php:278-291",
   "entry_point": "REST POST /issues (api/rest/restcore/issues_rest.php:169-181), SOAP mc_issue_add (api/soap/mc_issue_api.php:935-957), web POST bug_report.php:265",
   "module_kind": "command class / shared service layer"
  },
  {
   "where": "api/soap/mc_api.php:888-925",
   "entry_point": "shared converter mci_get_version_id(), called by both mc_issue_update (mc_issue_api.php:1039) and IssueAddCommand (IssueAddCommand.php:278,283,288)",
   "module_kind": "lower-level API helper - resolves id/name/string version shapes but never looks at the released flag or the caller's level"
  },
  {
   "where": "core/version_api.php:207-230,661-680",
   "entry_point": "internal producer: version_cache_row/version_get_field serve the 'released' column that a correct check must consult",
   "module_kind": "core API / version cache"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "bug_update.php:64-83"
 },
 "O3_reason_to_dismiss": "The web single-issue update has its own version validator, get_valid_version() (bug_update.php:72-83), which only checks that the name exists in the project; a solver can call this legacy root-level form handler unrelated to the REST/SOAP advisory, and the group-update page ships a VERSION_ALL list (bug_actiongroup_page.php:367-370) so the batch route looks intentionally unrestricted.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Partial updates must keep working when the stored version is already unreleased: REST PATCH merges the full issue body into the payload (issues_rest.php:436), so mc_issue_update re-submits the unchanged version on every edit, and a check that rejects any unreleased version breaks ordinary edits of issues a developer already put on an unreleased version. Separately, fixed_in_version is deliberately allowed to be unreleased - the update form and the resolve form print VERSION_ALL (bug_update_page.php:627, bug_change_status_page.php:335) - so extending the released check to that field breaks the resolve workflow.",
  "where": "api/rest/restcore/issues_rest.php:436"
 },
 "O6_input_shapes": [
  "REST object form {\"version\":{\"id\":<int>}}",
  "REST object form {\"version\":{\"name\":\"<version string>\"}}",
  "SOAP plain string version name (api/soap/mc_api.php:903-906)",
  "unset shapes that must stay allowed: null, \"\", [], {\"id\":0}, array without id/name (api/soap/mc_api.php:888-906, mc_issue_api.php:1035-1043)",
  "all three field names in one payload: version, target_version, fixed_in_version",
  "REST PATCH partial body merged with the stored issue (issues_rest.php:436) - unchanged values are resubmitted",
  "unknown version name/id falling back to webservice_version_when_not_found (api/soap/mc_api.php:909-922)"
 ],
 "O7_producer": {
  "kind": "cache",
  "where": "core/version_api.php:207-230",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Web batch update: POST bug_actiongroup.php with action UP_PRODUCT_VERSION (or UP_FIXED_IN_VERSION) checks only update_bug_threshold and version existence, then calls bug_set_field() for every selected issue; no released-status or report_issues_for_unreleased_versions_threshold check, and the action page offers VERSION_ALL to everyone.",
   "where": "bug_actiongroup.php:255-283",
   "reason_to_dismiss": "Batch actions are a separate web feature the REST/SOAP advisory never mentions, and bug_actiongroup_page.php:367-370 deliberately lists VERSION_ALL (including unreleased) for UP_PRODUCT_VERSION/UP_FIXED_IN_VERSION, so the route reads as intended behaviour.",
   "distance": "root-level web handler in a different directory tree from api/soap; no shared code with mc_issue_update",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Low-level assignment API bug_set_field() writes 'version', 'fixed_in_version' and 'target_version' verbatim (string case) straight to the DB, so any caller reaching it bypasses the released check; the group-update actions do exactly this.",
   "where": "core/bug_api.php:1977-1982,2007-2010",
   "reason_to_dismiss": "bug_set_field() is a generic field setter used across many features, arguably below the layer where an assignment policy belongs, and the advisory names only the REST and SOAP issue update.",
   "distance": "core/ API file, one layer below the command and API code, in a 2000+ line module",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "core/commands/IssueAddCommand.php:278-291",
   "sibling": "A new IssueUpdateCommand command class that copies the version block from IssueAddCommand but omits the released check",
   "why_realistic": "MantisBT is migrating REST work into command classes (IssueAddCommand, IssueNoteAddCommand, IssueNoteDeleteCommand already exist) while issue update still lives in mc_issue_update; a refactor would copy the add command's version block."
  },
  {
   "where": "bug_actiongroup.php:255-299",
   "sibling": "A fourth near-identical batch action (for example 'set build' or a per-field version action) copied from UP_PRODUCT_VERSION without the released check",
   "why_realistic": "Three near-identical version cases already sit side by side here and only UP_TARGET_VERSION carries an extra threshold, so copy-paste without the new check is the natural mistake."
  },
  {
   "where": "api/rest/restcore/issues_rest.php:37-46",
   "sibling": "A shortcut REST route such as PATCH /issues/{id}/version that writes the field through bug_set_field() instead of calling mc_issue_update",
   "why_realistic": "The file already exposes per-field sub-routes (tags, monitors, notes, files) and each is a thin handler that may bypass the full update path."
  }
 ],
 "O9_family": "Broken access control / authorization bypass through user-controlled key (CWE-639, CWE-863): a role-restricted field is assignable without any level check",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "composer (composer.json: PHP ^7.4||^8.0, slim/slim ^3, adodb, phpunit ^9.6-^11); phpunit.xml declares tests/Mantis, tests/soap and tests/rest suites; CI runs phpunit on PHP 7.4-8.x with MySQL and PostgreSQL (.github/workflows/mantisbt.yml:36,75-90)",
  "services": [
   "MySQL or PostgreSQL database",
   "HTTP server hosting the MantisBT instance for the rest/soap suites (tests/bootstrap.php.sample:23-26,81-86)"
  ],
  "offline_after_build": true,
  "project_tests": "phpunit.xml; unit suite tests/Mantis, integration suites tests/soap (IssueAddTest.php, VersionTest.php) and tests/rest (RestIssueTest.php, RestIssueUpdateVersion.php). The rest/soap suites require MANTIS_TESTSUITE_REST_HOST and MANTIS_TESTSUITE_API_TOKEN from a generated tests/bootstrap.php plus a live instance (tests/rest/RestBase.php:111-130)."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [
  "protection_documented_without_exceptions"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "api/soap/mc_issue_api.php, core/commands/IssueAddCommand.php, api/soap/mc_api.php, core/version_api.php (inferred - the supplied fix.diff is truncated to its commit header)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Guard only the version assignment the report points at in mc_issue_update (api/soap/mc_issue_api.php:1159), reproduce through PATCH /issues/{id} with {\"version\":{\"id\":N}}, and stop - leaving the REST/SOAP add path and the web handlers (bug_update.php, bug_actiongroup.php) open."
 },
 "out_of_scope_notes": [
  "The project-version CRUD API (api/soap/mc_project_api.php:379-416) is manager-gated version administration, a different sink from assigning a version to an issue; noted and not pursued."
 ],
 "unverified": [
  "The supplied fix diff (/home/mara/.tb-graders/cwe/stacking/screen-trees/scr-31647.fix.diff) contains only the commit header 'Prevent unauthorized update of version field' and no hunks, so the exact fix sites, whether tests were added, and whether the web routes were touched could not be read. fix_sites, O1 and O8 are reconstructed from the advisory summary plus the code at the pinned commit.",
  "repo_mb could not be measured (no shell in this session), so no tiny_repo/giant_repo flag was raised; MantisBT's tree is clearly far above 5 MB of source and far below 1.5 GB.",
  "regression_tests_in_pinned_commit: tests/rest/RestIssueUpdateVersion.php exists at the pinned commit and exercises version-field updates, but with an empty diff it cannot be compared with the fix's test files; not flagged.",
  "present_in_latest for the O8 routes: no latest release tree was supplied ('none'), so current presence is unknown.",
  "O7 check_calls_producer=false describes the pinned code (no server-side check exists at all; only the dropdown masks at bug_update_page.php:147-151 and bug_report_page.php:461-465 call the version list); the published fix's implementation was not readable.",
  "O12 protection_documented_without_exceptions is based on the unconditional wording 'Access level needed to assign bugs to unreleased product versions' (config_defaults_inc.php:3604-3609, docbook/Admin_Guide/en-US/config/misc.xml:480-483); note that bug_actiongroup_page.php:367-370 ships a VERSION_ALL list that contradicts enforcement there."
 ]
}
  ```
- Published fix sites:   - api/soap/mc_issue_api.php:1041-1043,1159-1163 — entry point: REST PATCH /issues/{id} (api/rest/restcore/issues_rest.php:407-439) and SOAP mc_issue_update (api/soap/mc_issue_api.php:971) [SOAP/REST API implementation layer]
  - core/commands/IssueAddCommand.php:278-291 — entry point: REST POST /issues (api/rest/restcore/issues_rest.php:169-181), SOAP mc_issue_add (api/soap/mc_issue_api.php:935-957), web POST bug_report.php:265 [command class / shared service layer]
  - api/soap/mc_api.php:888-925 — entry point: shared converter mci_get_version_id(), called by both mc_issue_update (mc_issue_api.php:1039) and IssueAddCommand (IssueAddCommand.php:278,283,288) [lower-level API helper - resolves id/name/string version shapes but never looks at the released flag or the caller's level]
  - core/version_api.php:207-230,661-680 — entry point: internal producer: version_cache_row/version_get_field serve the 'released' column that a correct check must consult [core API / version cache]
- Uncovered routes to confirm (pattern B):   - bug_actiongroup.php:255-283 — Web batch update: POST bug_actiongroup.php with action UP_PRODUCT_VERSION (or UP_FIXED_IN_VERSION) checks only update_bug_threshold and version existence, then calls bug_set_field() for every selected issue; no released-status or report_issues_for_unreleased_versions_threshold check, and the action page offers VERSION_ALL to everyone. (reason to dismiss: Batch actions are a separate web feature the REST/SOAP advisory never mentions, and bug_actiongroup_page.php:367-370 deliberately lists VERSION_ALL (including unreleased) for UP_PRODUCT_VERSION/UP_FIXED_IN_VERSION, so the route reads as intended behaviour.; still in latest: unknown)
  - core/bug_api.php:1977-1982,2007-2010 — Low-level assignment API bug_set_field() writes 'version', 'fixed_in_version' and 'target_version' verbatim (string case) straight to the DB, so any caller reaching it bypasses the released check; the group-update actions do exactly this. (reason to dismiss: bug_set_field() is a generic field setter used across many features, arguably below the layer where an assignment policy belongs, and the advisory names only the REST and SOAP issue update.; still in latest: unknown)
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

## Environment (`tasks/mantisbt-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/mantisbt-s2/instruction.md`)
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

## Tests (`tasks/mantisbt-s2/tests/`)
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
- **Wrong-fix patches** go in `build/mantisbt-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/mantisbt-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mantisbt-s2/manifest.json`:**
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

**Also in `build/mantisbt-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py mantisbt-s2 --only static
python3 -I common/gate/gate.py mantisbt-s2 --only nop
python3 -I common/gate/gate.py mantisbt-s2 --only oracle
python3 -I common/gate/gate.py mantisbt-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mantisbt-s2/`;
  - edit only `tasks/mantisbt-s2/`, `build/mantisbt-s2/` and, for pattern B, the register;
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
