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

Project root: `/home/mara/cwe-bench`. Task: `weblate-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2P9G-X3CV-5HH4", "CVE-2026-55227", "PYSEC-2026-3941"]; weblateorg/weblate; access control / object existence disclosure via unscoped lookup (IDOR-style oracle, CWE-203)
- Pinned (vulnerable) commit: ddc7e4d0107a059f99852126390d5bd9b9b9945a. Published fix: 836bc082803d49d02f2831ec8339268eb66bcdae.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "203",
 "advisory_ids": [
  "GHSA-2P9G-X3CV-5HH4",
  "CVE-2026-55227",
  "PYSEC-2026-3941"
 ],
 "repo": "weblateorg/weblate",
 "pinned_commit": "ddc7e4d0107a059f99852126390d5bd9b9b9945a",
 "fix_commits": [
  "836bc082803d49d02f2831ec8339268eb66bcdae"
 ],
 "trust_decision": {
  "summary": "Whether a user may learn that an object (unit, comment, check, change, announcement) in a private/blocked project exists is decided by the queryset passed to get_object_or_404 in each view; the views look up globally by pk and only afterwards run has_perm (403) or check_access_component (404), so existing-but-hidden objects answer differently from missing ones. The project-access filter itself is gated by User.needs_project_filter, which wrongly short-circuits for 'all projects' users who have a per-project block.",
  "evidence": [
   "weblate/trans/views/edit.py:933-936",
   "weblate/trans/views/changes.py:331-334",
   "weblate/auth/models.py:976-984",
   "weblate/trans/models/unit.py:422-433",
   "weblate/auth/models.py:925-929"
  ]
 },
 "landing_point": {
  "where": "weblate/trans/views/changes.py:331",
  "why": "Summary says 'globally scoped object lookups'; a grep for get_object_or_404(Model, pk=...) in trans/views lands on show_change/comment/js views first."
 },
 "fix_sites": [
  {
   "where": "weblate/trans/views/changes.py:331",
   "entry_point": "GET show_change (change/<pk>/)",
   "module_kind": "HTML view"
  },
  {
   "where": "weblate/trans/views/changes.py:335-338",
   "entry_point": "GET show_change ?other=<pk>&other=<pk> (list input)",
   "module_kind": "HTML view"
  },
  {
   "where": "weblate/trans/views/edit.py:933",
   "entry_point": "POST comment (comment/<pk>/)",
   "module_kind": "HTML/AJAX view"
  },
  {
   "where": "weblate/trans/views/edit.py:957",
   "entry_point": "POST delete-comment",
   "module_kind": "HTML/AJAX view"
  },
  {
   "where": "weblate/trans/views/edit.py:977",
   "entry_point": "POST resolve-comment",
   "module_kind": "HTML/AJAX view"
  },
  {
   "where": "weblate/trans/views/edit.py:1184",
   "entry_point": "POST delete-unit",
   "module_kind": "HTML view"
  },
  {
   "where": "weblate/trans/views/js.py:38",
   "entry_point": "GET js-unit-translations",
   "module_kind": "AJAX view"
  },
  {
   "where": "weblate/trans/views/js.py:61",
   "entry_point": "POST js-ignore-check",
   "module_kind": "AJAX view"
  },
  {
   "where": "weblate/trans/views/js.py:76",
   "entry_point": "POST js-ignore-check-source",
   "module_kind": "AJAX view"
  },
  {
   "where": "weblate/trans/views/js.py:109",
   "entry_point": "POST js-dismiss-automatically-translated",
   "module_kind": "AJAX view"
  },
  {
   "where": "weblate/trans/views/settings.py:484",
   "entry_point": "POST announcement-delete",
   "module_kind": "HTML view"
  },
  {
   "where": "weblate/trans/views/source.py:32",
   "entry_point": "POST edit_context",
   "module_kind": "HTML view"
  },
  {
   "where": "weblate/trans/models/announcement.py:131-133",
   "entry_point": "AnnouncementQuerySet (new filter_access, used by announcement-delete)",
   "module_kind": "model queryset (data layer)"
  },
  {
   "where": "weblate/auth/models.py:976-984",
   "entry_point": "User.needs_project_filter, consumed by every filter_access (Unit, Check, Screenshot, Suggestion, Component, Translation, Change)",
   "module_kind": "auth model / permission cache (lower-level, other package)"
  }
 ],
 "O1_entry_points": 11,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "weblate/auth/models.py:976-984 (needs_project_filter returns False for SELECTION_ALL users even when a UserBlock exists, so every QuerySet.filter_access skips the project filter, e.g. weblate/trans/models/unit.py:424, weblate/checks/models.py:66)"
 },
 "O3_reason_to_dismiss": "needs_project_filter is a performance shortcut in the auth package ('all projects' users can see every project), and the existing filter_access helpers are presumed correct, so a solver wrapping lookups in filter_access believes the job is done; the blocked-user-with-all-projects combination looks like an exotic neighbouring feature.",
 "O4_distance": {
  "files": 9,
  "packages": 5,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Global announcements (no project/category/component) must remain lookup-able so a non-privileged user still gets 403 rather than 404; show_change must still return 200 for an accessible change when ?other= contains hidden or non-integer pks (ignore, don't fail); superusers/'all projects' users without blocks must still reach private objects with no extra queries.",
  "where": "fix.diff:69-71, fix.diff:356-359, fix.diff:428-433, weblate/auth/models.py:978-981"
 },
 "O6_input_shapes": [
  "single pk path param",
  "repeated ?other= query list (multiple pks)",
  "non-integer ?other= values",
  "announcement scope shapes: global / project / category / component",
  "user shape: plain user vs SELECTION_ALL user with per-project UserBlock vs restricted component"
 ],
 "O7_producer": {
  "kind": "cache",
  "where": "weblate/auth/models.py:976-984 (cached_property needs_project_filter derived from project_permissions; blocked marker [(None, None)] at weblate/auth/models.py:896)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "machinery translate AJAX: global Unit lookup then has_perm('machinery.view') raises PermissionDenied (403 vs 404), no login_required",
   "where": "weblate/machinery/views.py:474-477",
   "reason_to_dismiss": "Machinery is a separate package/feature (MT services), not in trans/views; handle_machinery already checks permissions.",
   "distance": "other package (weblate/machinery) from weblate/trans/views",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "machinery memory AJAX: same global Unit lookup then 403 from handle_machinery",
   "where": "weblate/machinery/views.py:480-488",
   "reason_to_dismiss": "Translation-memory lookup is a neighbouring feature; same handler as translate.",
   "distance": "other package (weblate/machinery)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "glossary add term: global Unit lookup followed by check_access_component (404), same shape as fixed js.py:38",
   "where": "weblate/glossary/views.py:31-34",
   "reason_to_dismiss": "check_access_component already raises Http404, so status codes match; glossary is a separate app.",
   "distance": "other package (weblate/glossary)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "render-check AJAX: global Check.objects.get / Unit lookup before check_access_component (404)",
   "where": "weblate/checks/views.py:298-305",
   "reason_to_dismiss": "Already 404s via check_access_component; checks app, read-only render.",
   "distance": "other package (weblate/checks)",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "weblate/trans/views/edit.py:587",
   "sibling": "suggestion action lookup by pk without unit scoping (Suggestion.objects.get(pk=sugid))",
   "why_realistic": "Suggestion has its own filter_access (weblate/trans/models/suggestion.py:104); a maintainer dropping unit=unit in a refactor is plausible."
  },
  {
   "where": "weblate/trans/models/change.py:331-334",
   "sibling": "a second 'skip filter' shortcut like needs_project_filter that ignores blocked ids",
   "why_realistic": "filter_projects already gates on needs_project_filter; a parallel cached shortcut for categories/workspaces is a natural performance optimisation."
  },
  {
   "where": "weblate/screenshots/views.py:480",
   "sibling": "screenshot AJAX view using bare get_object_or_404(Screenshot, pk=pk)",
   "why_realistic": "Neighbouring screenshot views use filter_access; one new endpoint forgetting it is a common slip."
  }
 ],
 "O9_family": "access control / object existence disclosure via unscoped lookup (IDOR-style oracle, CWE-203)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "Python 3 + Django, uv/pip install of weblate with test extras",
  "services": [
   "postgresql",
   "redis (cache/celery; possibly replaceable in test settings)"
  ],
  "offline_after_build": true,
  "project_tests": "weblate/trans/tests/test_changes.py, test_comment.py, test_edit.py, test_js_views.py, test_manage.py, test_views.py, weblate/auth/tests/test_models.py (Django TestCase with fixtures)"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "weblate/auth/models.py, weblate/trans/models/announcement.py, weblate/trans/views/changes.py, weblate/trans/views/edit.py, weblate/trans/views/js.py, weblate/trans/views/settings.py, weblate/trans/views/source.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Wrap each get_object_or_404(Model, pk) in trans/views with Model.objects.filter_access(user), trusting filter_access/needs_project_filter and leaving machinery/glossary/checks views and blocked all-projects users open."
 },
 "out_of_scope_notes": [
  "Workspace/billing views use bare get_object_or_404 (weblate/workspaces/views.py:87, weblate/billing/views.py:87,235,286); different protection model, not pursued."
 ],
 "unverified": [
  "repo_mb not measured.",
  "Whether glossary/render-check routes are observably distinguishable (both already return 404 via check_access_component; may differ only in message/timing) \u2014 listed as consistency siblings of the fixed js.py:38.",
  "Test services: PostgreSQL requirement and whether Redis is needed in test settings not confirmed from settings files.",
  "present_in_latest unknown for all O8 routes (no latest release provided).",
  "O1 counts 11 HTTP entry points (show_change, comment, delete-comment, resolve-comment, delete-unit, js-unit-translations, js-ignore-check, js-ignore-check-source, js-dismiss-automatically-translated, announcement-delete, edit_context)."
 ]
}
  ```
- Published fix sites:   - weblate/trans/views/changes.py:331 — entry point: GET show_change (change/<pk>/) [HTML view]
  - weblate/trans/views/changes.py:335-338 — entry point: GET show_change ?other=<pk>&other=<pk> (list input) [HTML view]
  - weblate/trans/views/edit.py:933 — entry point: POST comment (comment/<pk>/) [HTML/AJAX view]
  - weblate/trans/views/edit.py:957 — entry point: POST delete-comment [HTML/AJAX view]
  - weblate/trans/views/edit.py:977 — entry point: POST resolve-comment [HTML/AJAX view]
  - weblate/trans/views/edit.py:1184 — entry point: POST delete-unit [HTML view]
  - weblate/trans/views/js.py:38 — entry point: GET js-unit-translations [AJAX view]
  - weblate/trans/views/js.py:61 — entry point: POST js-ignore-check [AJAX view]
  - weblate/trans/views/js.py:76 — entry point: POST js-ignore-check-source [AJAX view]
  - weblate/trans/views/js.py:109 — entry point: POST js-dismiss-automatically-translated [AJAX view]
  - weblate/trans/views/settings.py:484 — entry point: POST announcement-delete [HTML view]
  - weblate/trans/views/source.py:32 — entry point: POST edit_context [HTML view]
  - weblate/trans/models/announcement.py:131-133 — entry point: AnnouncementQuerySet (new filter_access, used by announcement-delete) [model queryset (data layer)]
  - weblate/auth/models.py:976-984 — entry point: User.needs_project_filter, consumed by every filter_access (Unit, Check, Screenshot, Suggestion, Component, Translation, Change) [auth model / permission cache (lower-level, other package)]
- Uncovered routes to confirm (pattern B):   - weblate/machinery/views.py:474-477 — machinery translate AJAX: global Unit lookup then has_perm('machinery.view') raises PermissionDenied (403 vs 404), no login_required (reason to dismiss: Machinery is a separate package/feature (MT services), not in trans/views; handle_machinery already checks permissions.; still in latest: unknown)
  - weblate/machinery/views.py:480-488 — machinery memory AJAX: same global Unit lookup then 403 from handle_machinery (reason to dismiss: Translation-memory lookup is a neighbouring feature; same handler as translate.; still in latest: unknown)
  - weblate/glossary/views.py:31-34 — glossary add term: global Unit lookup followed by check_access_component (404), same shape as fixed js.py:38 (reason to dismiss: check_access_component already raises Http404, so status codes match; glossary is a separate app.; still in latest: unknown)
  - weblate/checks/views.py:298-305 — render-check AJAX: global Check.objects.get / Unit lookup before check_access_component (404) (reason to dismiss: Already 404s via check_access_component; checks app, read-only render.; still in latest: unknown)
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

## Environment (`tasks/weblate-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/weblate-ds/instruction.md`)
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

## Tests (`tasks/weblate-ds/tests/`)
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
- **Wrong-fix patches** go in `build/weblate-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/weblate-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/weblate-ds/manifest.json`:**
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

**Also in `build/weblate-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py weblate-ds --only static
python3 -I builder/gate.py weblate-ds --only nop
python3 -I builder/gate.py weblate-ds --only oracle
python3 -I builder/gate.py weblate-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/weblate-ds/`;
  - edit only `tasks/weblate-ds/`, `build/weblate-ds/` and, for pattern B, the register;
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
