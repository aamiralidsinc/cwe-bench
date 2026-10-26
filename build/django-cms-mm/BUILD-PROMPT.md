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

Project root: `/home/mara/cwe-bench`. Task: `django-cms-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-6X92-6VX4-5FWR", "CVE-2026-63003", "PYSEC-2026-3821"]; django-cms/django-cms; missing object-level authorization (IDOR) on a client-controlled form field selecting the copy source / target page (CWE-639/CWE-862)
- Pinned (vulnerable) commit: unknown (parent of 3e1ccf7573eb1a74ebbbfaaa812c1f5cadf14e6c; no .git in the pinned tree). Published fix: 3e1ccf7573eb1a74ebbbfaaa812c1f5cadf14e6c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "1609",
 "advisory_ids": [
  "GHSA-6X92-6VX4-5FWR",
  "CVE-2026-63003",
  "PYSEC-2026-3821"
 ],
 "repo": "django-cms/django-cms",
 "pinned_commit": "unknown (parent of 3e1ccf7573eb1a74ebbbfaaa812c1f5cadf14e6c; no .git in the pinned tree)",
 "fix_commits": [
  "3e1ccf7573eb1a74ebbbfaaa812c1f5cadf14e6c"
 ],
 "trust_decision": {
  "summary": "Whether the requesting staff user may read (view) the client-chosen source page whose placeholders/plugins/extensions the add/duplicate form copies into a new page, and may change the client-chosen existing page (cms_page) a translation is added to; decided in the AddPageForm family's field cleaning in cms/admin/forms.py, while the admin view only checks generic add-page permission.",
  "evidence": [
   "cms/admin/forms.py:514-519",
   "cms/admin/forms.py:248-257",
   "cms/admin/forms.py:397-424",
   "cms/admin/forms.py:367-378",
   "cms/admin/pageadmin.py:906-921",
   "cms/admin/pageadmin.py:1015-1040",
   "fix.diff:54-68",
   "fix.diff:41-45"
  ]
 },
 "landing_point": {
  "where": "cms/admin/forms.py:514",
  "why": "The summary names page *Duplicate*; DuplicatePageForm (hidden source over Page.objects.all()) is the form behind the duplicate admin route at cms/admin/pageadmin.py:834,906-921."
 },
 "fix_sites": [
  {
   "where": "cms/admin/forms.py:514-519",
   "entry_point": "POST /admin/cms/pagecontent/<id>/duplicate/ (PageContentAdmin.duplicate -> add_view, hidden source field)",
   "module_kind": "admin form (landing)"
  },
  {
   "where": "cms/admin/forms.py:279-287",
   "entry_point": "POST /admin/cms/pagecontent/add/ (Add translation, cms_page) and duplicate route; also cms wizard via CreateCMSPageForm(AddPageForm); fix moves cms_page site narrowing before the hidden-source early return (fix.diff:20-32)",
   "module_kind": "shared base form __init__ (field queryset/schema)"
  },
  {
   "where": "cms/admin/forms.py:334-338",
   "entry_point": "same as above; fix adds AddPageForm.clean_cms_page requiring change permission on the existing page (fix.diff:41-45)",
   "module_kind": "shared base form clean (neighbouring 'add translation' feature)"
  },
  {
   "where": "cms/admin/forms.py:1309",
   "entry_point": "PageUserGroup/PageUser admin add/change (GenericCmsPermissionForm.clean) - bundled, separate CWE-269 fix (fix.diff:89-114)",
   "module_kind": "unrelated bundled fix"
  },
  {
   "where": "cms/forms/validators.py:22-29",
   "entry_point": "validate_url used by URL/redirect fields - bundled, separate CWE-79 fix (fix.diff:135-149)",
   "module_kind": "unrelated bundled fix"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "cms/admin/forms.py:253-257,279-287 (cms_page on the shared AddPageForm base, inherited by DuplicatePageForm at cms/admin/forms.py:514 and the wizard form at cms/forms/wizards.py:22); fixed at fix.diff:20-32,41-45 under the 'Add translation' feature, not Duplicate"
 },
 "O3_reason_to_dismiss": "cms_page belongs to the 'Add translation' feature, not Duplicate, and visible page-type 'source' choices are shared templates any page creator may build on - so a solver fixing 'duplicate reads any page' can argue both are a different feature.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Users allowed to add pages must still be able to (a) duplicate pages they can view/change, (b) create pages from this site's page types via the visible source select, and (c) add a translation to a page they can change; the tree copy route copies across sites for users who can view the source. An over-broad fix (requiring superuser/change on every source, site-filtering source for all copies, or rejecting cms_page outright) breaks these.",
  "where": "cms/admin/forms.py:289-302; cms/admin/forms.py:397-404; cms/admin/pageadmin.py:931-939; cms/admin/pageadmin.py:664-673"
 },
 "O6_input_shapes": [
  "source pk supplied in POST body (hidden field) rather than via the URL-derived GET initial (cms/admin/pageadmin.py:915-920)",
  "cms_page pk from another site / a page the user cannot change, in POST or GET (cms/admin/pageadmin.py:931-933)",
  "form variant where the source widget is hidden (fewer than 2 page types, or hidden-source subclasses) which hit the early return that skipped cms_page site narrowing (cms/admin/forms.py:281-287, fix.diff:20-32)"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "cms/admin/forms.py:248-257 and cms/admin/forms.py:515-518 (ModelChoiceField querysets Page.objects.filter(is_page_type=True) / Page.objects.all() define what source/cms_page values are accepted; only the widget choices are narrowed at cms/admin/forms.py:295-297)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "AddPageForm visible 'source' page-type select: queryset spans page types of every site and has no view check; only the rendered choices are narrowed to this site",
   "where": "cms/admin/forms.py:248-252",
   "reason_to_dismiss": "Page types are shared templates meant to be copied; the dropdown already lists only this site's page types, and the report is about Duplicate.",
   "distance": "same file, different class (base of the landing form); reached via the plain add view, cms/admin/pageadmin.py:775,923",
   "present_in_latest": "no",
   "latest_where": "latest/cms/admin/forms.py:316-322"
  },
  {
   "route": "Page wizard (CreateCMSPageForm) inherits the same unchecked page-type source and copies it via AddPageForm.save; the wizard itself only checks add-page permission",
   "where": "cms/forms/wizards.py:22",
   "reason_to_dismiss": "Wizards are a separate frontend feature in another package; clean_parent_page there already does a permission check (cms/forms/wizards.py:102-125).",
   "distance": "other package (cms.forms / cms.cms_wizards vs cms.admin); registered at cms/cms_wizards.py:44",
   "present_in_latest": "no",
   "latest_where": "latest/cms/admin/forms.py:381-389"
  },
  {
   "route": "AddPageTypeForm hidden 'source' over Page.objects.all() copies any page into a page type with permissions=False and no view/change check",
   "where": "cms/admin/forms.py:445-453",
   "reason_to_dismiss": "Legacy class not wired into any in-tree admin (only subclass users reach it), so it looks out of scope.",
   "distance": "same file, sibling class between AddPageForm and DuplicatePageForm (cms/admin/forms.py:492-502)",
   "present_in_latest": "no",
   "latest_where": "latest/cms/admin/forms.py:542"
  },
  {
   "route": "cms_page + source together: save() reuses the existing page and copies source placeholders into the new translation, skipping from_source()",
   "where": "cms/admin/forms.py:397-424",
   "reason_to_dismiss": "Unsupported combination - the UI never sends both a translation target and a source.",
   "distance": "same file, AddPageForm.save",
   "present_in_latest": "no",
   "latest_where": "latest/cms/admin/forms.py:336-340"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "cms/admin/pageadmin.py:851-856",
   "sibling": "Wire a 'save as page type' / 'create from page' admin route that uses AddPageTypeForm's hidden source like duplicate_form does",
   "why_realistic": "get_form_class already dispatches on path_info for duplicate; a page-type route is the obvious next form and AddPageTypeForm already exists unused at cms/admin/forms.py:445."
  },
  {
   "where": "cms/forms/wizards.py:22-47",
   "sibling": "A 'page from existing page' wizard field with a hidden source over Page.objects.all()",
   "why_realistic": "The wizard already reuses AddPageForm's source/copy machinery and only re-checks parent permissions in clean_parent_page."
  }
 ],
 "O9_family": "missing object-level authorization (IDOR) on a client-controlled form field selecting the copy source / target page (CWE-639/CWE-862)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "pip + Django (test_requirements/django-4.2.txt .. django-5.2.txt, test_requirements/requirements_base.txt), setup.py/pyproject.toml; tests via manage.py/testserver.py",
  "services": [],
  "offline_after_build": true,
  "project_tests": "cms/tests/test_forms.py (fix adds DuplicatePageFormSecurityTestCase/AddPageFormSecurityTestCase), cms/tests/test_page_admin.py, cms/tests/test_wizards.py; sqlite by default (test_requirements/databases.txt lists optional DBs)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "cms/admin/forms.py, cms/forms/validators.py (validators.py change is a bundled, unrelated XSS fix)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a user_can_view_page check on source only in DuplicatePageForm (or in the duplicate view on the URL object), leaving cms_page, the page-type source on AddPageForm/wizard, and AddPageTypeForm open."
 },
 "out_of_scope_notes": [
  "Fix commit bundles a CWE-269 group-permission escalation fix in GenericCmsPermissionForm (fix.diff:89-114) - separate advisory, not pursued.",
  "Fix commit bundles a CWE-79 javascript:-scheme bypass in validate_url (fix.diff:135-149) - separate advisory, not pursued.",
  "copy_page tree route checks view permission against a client-supplied source_site (cms/admin/pageadmin.py:662-665) - not pursued."
 ],
 "unverified": [
  "pinned_commit hash unknown: no .git directory in the pinned tree.",
  "repo_mb unknown: size not measured (no shell).",
  "recall_risk is a judgement: advisory published 2026-08-20; extent of public write-ups not checked.",
  "The published fix checks only user_can_view_page for the duplicate source; latest upstream requires change permission on the source for hidden-source forms (latest/cms/admin/forms.py:377-378), so the published check may itself be weaker than the final one - not verified against advisory text.",
  "O7 check_calls_producer=true relies on Django ModelChoiceField validating against the queryset (not the widget choices); not run.",
  "Whether page types from another site are actually reachable through the add view's has_add_permission (cms/admin/pageadmin.py:1015-1040) was not exercised."
 ]
}
  ```
- Published fix sites:   - cms/admin/forms.py:514-519 — entry point: POST /admin/cms/pagecontent/<id>/duplicate/ (PageContentAdmin.duplicate -> add_view, hidden source field) [admin form (landing)]
  - cms/admin/forms.py:279-287 — entry point: POST /admin/cms/pagecontent/add/ (Add translation, cms_page) and duplicate route; also cms wizard via CreateCMSPageForm(AddPageForm); fix moves cms_page site narrowing before the hidden-source early return (fix.diff:20-32) [shared base form __init__ (field queryset/schema)]
  - cms/admin/forms.py:334-338 — entry point: same as above; fix adds AddPageForm.clean_cms_page requiring change permission on the existing page (fix.diff:41-45) [shared base form clean (neighbouring 'add translation' feature)]
  - cms/admin/forms.py:1309 — entry point: PageUserGroup/PageUser admin add/change (GenericCmsPermissionForm.clean) - bundled, separate CWE-269 fix (fix.diff:89-114) [unrelated bundled fix]
  - cms/forms/validators.py:22-29 — entry point: validate_url used by URL/redirect fields - bundled, separate CWE-79 fix (fix.diff:135-149) [unrelated bundled fix]
- Uncovered routes to confirm (pattern B):   - cms/admin/forms.py:248-252 — AddPageForm visible 'source' page-type select: queryset spans page types of every site and has no view check; only the rendered choices are narrowed to this site (reason to dismiss: Page types are shared templates meant to be copied; the dropdown already lists only this site's page types, and the report is about Duplicate.; still in latest: no)
  - cms/forms/wizards.py:22 — Page wizard (CreateCMSPageForm) inherits the same unchecked page-type source and copies it via AddPageForm.save; the wizard itself only checks add-page permission (reason to dismiss: Wizards are a separate frontend feature in another package; clean_parent_page there already does a permission check (cms/forms/wizards.py:102-125).; still in latest: no)
  - cms/admin/forms.py:445-453 — AddPageTypeForm hidden 'source' over Page.objects.all() copies any page into a page type with permissions=False and no view/change check (reason to dismiss: Legacy class not wired into any in-tree admin (only subclass users reach it), so it looks out of scope.; still in latest: no)
  - cms/admin/forms.py:397-424 — cms_page + source together: save() reuses the existing page and copies source placeholders into the new translation, skipping from_source() (reason to dismiss: Unsupported combination - the UI never sends both a translation target and a source.; still in latest: no)
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

## Environment (`tasks/django-cms-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/django-cms-mm/instruction.md`)
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

## Tests (`tasks/django-cms-mm/tests/`)
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
- **Wrong-fix patches** go in `build/django-cms-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/django-cms-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/django-cms-mm/manifest.json`:**
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

**Also in `build/django-cms-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py django-cms-mm --only static
python3 -I builder/gate.py django-cms-mm --only nop
python3 -I builder/gate.py django-cms-mm --only oracle
python3 -I builder/gate.py django-cms-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/django-cms-mm/`;
  - edit only `tasks/django-cms-mm/`, `build/django-cms-mm/` and, for pattern B, the register;
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
