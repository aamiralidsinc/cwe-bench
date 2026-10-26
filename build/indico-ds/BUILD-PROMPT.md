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

Project root: `/home/mara/cwe-bench`. Task: `indico-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-C4WC-GGRJ-JG9V", "CVE-2026-107396"]; indico/indico; XSS (CWE-79-like): javascript:-scheme URLs in href and unsanitized stored HTML in a serializer output
- Pinned (vulnerable) commit: 3c69cba9b1d1dc7ae46e289ae39403597583ec3d. Published fix: d4c8c7127176efa4cb53c64119ca8ee2b551be18.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "2691",
 "advisory_ids": [
  "GHSA-C4WC-GGRJ-JG9V",
  "CVE-2026-107396"
 ],
 "repo": "indico/indico",
 "pinned_commit": "3c69cba9b1d1dc7ae46e289ae39403597583ec3d",
 "fix_commits": [
  "d4c8c7127176efa4cb53c64119ca8ee2b551be18"
 ],
 "trust_decision": {
  "summary": "Which user-entered URLs may go into href attributes (only http/https, no javascript:), decided in the WTForms field validators for attachment links, menu links and the link-list field; and whether stored note HTML is sanitized before the notes JSON serializer hands it to the React editor/conflict modal (dangerouslySetInnerHTML).",
  "evidence": [
   "indico/modules/attachments/forms.py:94",
   "indico/modules/events/layout/forms.py:204",
   "indico/web/forms/fields/simple.py:230-234",
   "indico/modules/events/notes/schemas.py:12-25",
   "indico/web/client/js/react/components/notes/ConflictModal.jsx:141",
   "indico/modules/attachments/templates/_display.html:21",
   "indico/modules/events/layout/templates/_menu.html:89"
  ]
 },
 "landing_point": {
  "where": "indico/modules/attachments/forms.py:94",
  "why": "\"link fields\" points to the link attachment form, link_url = URLField with only DataRequired(), rendered as href at indico/modules/attachments/templates/_display.html:21"
 },
 "fix_sites": [
  {
   "where": "indico/modules/attachments/forms.py:94",
   "entry_point": "POST /event|/category/<id>/.../attachments/add/link and .../attachments/<folder_id>/<attachment_id>/ (indico/modules/attachments/blueprint.py:74-79)",
   "module_kind": "handler form (WTForms mixin shared by add and edit)"
  },
  {
   "where": "indico/modules/events/layout/forms.py:204",
   "entry_point": "event menu add/edit user link, RHMenuAddEntry / RHMenuEntryEdit (indico/modules/events/layout/controllers/menu.py:233-244, 113-126)",
   "module_kind": "handler form"
  },
  {
   "where": "indico/web/forms/fields/simple.py:230-234",
   "entry_point": "event privacy settings, EventPrivacyForm.privacy_policy_urls (indico/modules/events/management/forms.py:246, indico/modules/events/management/controllers/privacy.py:26)",
   "module_kind": "generic form-field library (lower-level, in indico/web)"
  },
  {
   "where": "indico/modules/events/notes/schemas.py:12-17",
   "entry_point": "notes API GET/POST/DELETE RHApiNote and the conflict path check_note_revision (indico/modules/events/notes/controllers.py:69,98,109; indico/modules/events/notes/util.py:99,105)",
   "module_kind": "marshmallow serializer"
  },
  {
   "where": "indico/modules/events/notes/schemas.py:20-25",
   "entry_point": "compile minutes RHApiCompileNotes (indico/modules/events/notes/controllers.py:115)",
   "module_kind": "marshmallow serializer"
  }
 ],
 "O1_entry_points": 8,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "indico/modules/events/notes/schemas.py:12-25 (note HTML serializer feeding indico/web/client/js/react/components/notes/ConflictModal.jsx:141 and NoteEditor.jsx:52); display paths already sanitize at indico/modules/events/notes/templates/_note.html:38 and indico/modules/events/notes/controllers.py:59"
 },
 "O3_reason_to_dismiss": "The report is about link fields and note display is already sanitized (_note.html:38, controllers.py:59), so the JSON serializer for the editor looks like an internal API that only returns the user's own editable data rather than an XSS sink.",
 "O4_distance": {
  "files": 4,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Sanitizing must keep allowed markup (e.g. <img src> kept with only the handler removed), and the source field must stay raw so editing still works. Link fields must keep accepting ordinary http/https links. ReferenceType deliberately allows non-http schemes, so an over-broad global URL scheme filter would break it.",
  "where": "fix.diff:123-127; indico/modules/events/notes/schemas.py:15; indico/modules/events/forms.py:37-40"
 },
 "O6_input_shapes": [
  "single URL string in a WTForms URLField (attachment link add/edit, menu link add/edit)",
  "JSON list of {title,url} objects in IndicoLinkListField, every element checked (single and multi-link lists)",
  "note HTML in single-object dump (EventNoteSchema) and many=True list dump (CompiledEventNoteSchema)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "indico/modules/events/notes/schemas.py:12-25",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Note-conflict response returns html=render_note(submitted source) without sanitizing, and ConflictModal renders it with dangerouslySetInnerHTML; the submitted source can come from another user's raw note source (EventNoteSchema 'source' stays unsanitized).",
   "where": "indico/modules/events/notes/util.py:101",
   "reason_to_dismiss": "It renders the submitting user's own input (self-XSS), and the fix only sanitized the stored 'html' of the conflicting revision.",
   "distance": "same package as the notes fix site (events/notes), different file; JS sink in indico/web/client/js/react/components/notes/ConflictModal.jsx:120",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Event/category cloning copies stored link_url values of menu entries (and attachments) without re-validating; those values are rendered as href unchanged",
   "where": "indico/modules/events/layout/clone.py:68",
   "reason_to_dismiss": "Clone only copies data that already passed form validation; legacy pre-fix data is a migration concern",
   "distance": "separate clone module in events/layout; attachments counterpart indico/modules/attachments/clone.py:102",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "indico/modules/events/management/forms.py:171",
   "sibling": "Event own_map_url URLField rendered as href at indico/modules/events/templates/display/conference.html:59; in our copy drop URL() or use a raw StringField",
   "why_realistic": "Same URLField idiom as the two fixed fields; a maintainer adding a location link field could easily copy the pre-fix DataRequired-only pattern"
  },
  {
   "where": "indico/web/forms/fields/simple.py:218-234",
   "sibling": "A second link-list style JSON field (e.g. extra event links) reusing JSONField without the scheme check, or the scheme check done before process_formdata normalisation",
   "why_realistic": "IndicoLinkListField is generic and its widget is reusable; a new form could subclass JSONField directly"
  },
  {
   "where": "indico/modules/events/notes/schemas.py:20-25",
   "sibling": "Another dump schema of EventNoteRevision/EventPage html (e.g. a page-content API) without the post_dump sanitizer",
   "why_realistic": "Display templates already sanitize via the |sanitize_html filter (indico/modules/events/layout/templates/page.html:23), so a maintainer would assume HTML is safe at the model level"
  }
 ],
 "O9_family": "XSS (CWE-79-like): javascript:-scheme URLs in href and unsanitized stored HTML in a serializer output",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (Flask/SQLAlchemy) + React/JS frontend",
  "toolchain": "pip with pinned requirements.txt (wtforms==3.2.1 at requirements.txt:400, marshmallow==3.26.2 at requirements.txt:202), pytest; npm/webpack only needed for the JS assets",
  "services": [
   "PostgreSQL (for DB-backed tests)",
   "Redis (app runtime)"
  ],
  "offline_after_build": true,
  "project_tests": "pytest; notes model tests at indico/modules/events/notes/models/notes_test.py; the fix adds indico/modules/events/notes/schemas_test.py (pure schema dump, no DB). Form-level tests for the link fields: unknown"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "indico/modules/attachments/forms.py, indico/modules/events/layout/forms.py, indico/web/forms/fields/simple.py, indico/modules/events/notes/schemas.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add URL() to the attachment link_url field only (the report's example) and miss the menu link form, the generic IndicoLinkListField list and the notes serializer."
 },
 "out_of_scope_notes": [
  "CLI event YAML import (indico/cli/event.py:131 -> indico/modules/events/export.py:115) writes raw rows including link_url; it is operator-only.",
  "ReferenceType.url_template (indico/modules/events/forms.py:37) is a URLField without URL(); it is admin-only and non-http schemes are allowed on purpose."
 ],
 "unverified": [
  "WTForms 3.2.1 URL() checks only a ^[a-z]+:// regex plus hostname validation, so a value like javascript://host.tld/%0a... may still pass the fixed attachment/menu fields. Library source was not available offline. If true, the published fix is itself incomplete: hidden tests must not assert that it rejects this, or the reference fix would fail them.",
  "IndicoLinkListField check uses case-sensitive startswith (fix.diff:136), so uppercase HTTPS:// links are rejected; whether that counts as a legit-behaviour regression is unverified.",
  "Whether TinyMCE strips event handlers when the unsanitized 'source' (indico/modules/events/notes/schemas.py:15) is loaded into the editor (NoteEditor.jsx:85) was not checked; this decides whether O8 route 1 is cross-user or self-only.",
  "O1 counts 8 entry points: attachment add-link, attachment edit, menu add, menu edit, privacy settings, notes GET, notes POST/DELETE (incl. conflict), compile notes. Attachment routes are multiplied per object type (indico/modules/attachments/blueprint.py:55-79).",
  "repo_mb not measured; present_in_latest unknown because no latest release was given."
 ]
}
  ```
- Published fix sites:   - indico/modules/attachments/forms.py:94 — entry point: POST /event|/category/<id>/.../attachments/add/link and .../attachments/<folder_id>/<attachment_id>/ (indico/modules/attachments/blueprint.py:74-79) [handler form (WTForms mixin shared by add and edit)]
  - indico/modules/events/layout/forms.py:204 — entry point: event menu add/edit user link, RHMenuAddEntry / RHMenuEntryEdit (indico/modules/events/layout/controllers/menu.py:233-244, 113-126) [handler form]
  - indico/web/forms/fields/simple.py:230-234 — entry point: event privacy settings, EventPrivacyForm.privacy_policy_urls (indico/modules/events/management/forms.py:246, indico/modules/events/management/controllers/privacy.py:26) [generic form-field library (lower-level, in indico/web)]
  - indico/modules/events/notes/schemas.py:12-17 — entry point: notes API GET/POST/DELETE RHApiNote and the conflict path check_note_revision (indico/modules/events/notes/controllers.py:69,98,109; indico/modules/events/notes/util.py:99,105) [marshmallow serializer]
  - indico/modules/events/notes/schemas.py:20-25 — entry point: compile minutes RHApiCompileNotes (indico/modules/events/notes/controllers.py:115) [marshmallow serializer]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/indico-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/indico-ds/instruction.md`)
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

## Tests (`tasks/indico-ds/tests/`)
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
- **Wrong-fix patches** go in `build/indico-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/indico-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/indico-ds/manifest.json`:**
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

**Also in `build/indico-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py indico-ds --only static
python3 -I builder/gate.py indico-ds --only nop
python3 -I builder/gate.py indico-ds --only oracle
python3 -I builder/gate.py indico-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/indico-ds/`;
  - edit only `tasks/indico-ds/`, `build/indico-ds/` and, for pattern B, the register;
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
