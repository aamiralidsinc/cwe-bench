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

Project root: `/home/mara/cwe-bench`. Task: `generator-jhipster-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-9FFP-22J7-56R2", "CVE-2026-107303"]; jhipster/generator-jhipster; CWE-79 stored XSS via attacker-controlled MIME type of a same-origin blob: URL (content-type allowlist / sniffing)
- Pinned (vulnerable) commit: bc2f089c9d44e96072346a716b8960a907236ebd. Published fix: efe95edd4dedc3379735094936439410a51ce3d9.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "10275",
 "advisory_ids": [
  "GHSA-9FFP-22J7-56R2",
  "CVE-2026-107303"
 ],
 "repo": "jhipster/generator-jhipster",
 "pinned_commit": "bc2f089c9d44e96072346a716b8960a907236ebd",
 "fix_commits": [
  "efe95edd4dedc3379735094936439410a51ce3d9"
 ],
 "trust_decision": {
  "summary": "The user-stored blob ContentType decides the MIME type of a same-origin blob: URL opened in a new window. At the pinned commit the generated client's shared openFile helper passes it through unchanged, so a stored text/html or image/svg+xml blob runs script under the app origin. The fix allowlists raster image/* (not +xml) for image blobs and text/plain for text blobs, and forces application/octet-stream for everything else.",
  "evidence": [
   "generators/client/generators/common/templates/src/main/webapp/app/shared/jhipster/data-utils.ts.ejs:49-62",
   "fix.diff:214-226",
   "fix.diff:237"
  ]
 },
 "landing_point": {
  "where": "generators/client/generators/common/templates/src/main/webapp/app/shared/jhipster/data-utils.ts.ejs:58-60",
  "why": "The only place where a Blob is built with the stored contentType and opened through globalThis.open. A search for createObjectURL/openFile leads here first."
 },
 "fix_sites": [
  {
   "where": "generators/client/generators/common/templates/src/main/webapp/app/shared/jhipster/data-utils.ts.ejs:49-60",
   "entry_point": "generated app: openFile(data, contentType) shared helper (all clients), reached by clicking an entity blob/image link",
   "module_kind": "shared client helper template (core sink)"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/core/util/data-util.service.ts.ejs:48-49",
   "entry_point": "Angular DataUtils.openFile service API",
   "module_kind": "Angular wrapper service"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/detail/_entityFile_-detail.html.ejs:52",
   "entry_point": "Angular entity detail page, image blob click",
   "module_kind": "Angular view template"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/detail/_entityFile_-detail.ts.ejs:81-82",
   "entry_point": "Angular entity detail component openFile",
   "module_kind": "Angular component wrapper"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/list/_entityFile_.html.ejs:124",
   "entry_point": "Angular entity list page, image blob click",
   "module_kind": "Angular view template"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/list/_entityFile_.ts.ejs:279-280",
   "entry_point": "Angular entity list component openFile",
   "module_kind": "Angular component wrapper"
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/update/_entityFile_-update.ts.ejs:177-178",
   "entry_point": "Angular entity update component openFile (update form 'open' link)",
   "module_kind": "Angular component wrapper"
  },
  {
   "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-detail.tsx.ejs:26",
   "entry_point": "React entity detail page blob/image click (was react-jhipster openFile)",
   "module_kind": "React view; switches from external library implementation to local helper"
  },
  {
   "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-detail.tsx.ejs:99",
   "entry_point": "React entity detail page blob/image click",
   "module_kind": "React view"
  },
  {
   "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.tsx.ejs:28",
   "entry_point": "React entity list page blob/image click (was react-jhipster openFile)",
   "module_kind": "React view; switches implementation"
  },
  {
   "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.tsx.ejs:420",
   "entry_point": "React entity list page blob/image click",
   "module_kind": "React view"
  },
  {
   "where": "generators/vue/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-details.vue.ejs:17",
   "entry_point": "Vue entity details page, image blob click",
   "module_kind": "Vue view template"
  },
  {
   "where": "generators/vue/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.vue.ejs:70",
   "entry_point": "Vue entity list page, image blob click",
   "module_kind": "Vue view template"
  },
  {
   "where": "generators/vue/templates/src/main/webapp/app/shared/data/data-utils.service.ts.ejs:46-47",
   "entry_point": "Vue useDataUtils().openFile composable API (argument order reversed: contentType, data)",
   "module_kind": "Vue wrapper composable"
  }
 ],
 "O1_entry_points": 12,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-detail.tsx.ejs:22-34 and generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.tsx.ejs:25-40 (React imports openFile from the react-jhipster npm package, not the local shared helper at generators/client/generators/common/templates/src/main/webapp/app/shared/jhipster/data-utils.ts.ejs:49, even though that helper is generated for every client per generators/client/generators/common/generator.ts:41)"
 },
 "O3_reason_to_dismiss": "React's openFile comes from the third-party react-jhipster dependency, not from code in this repo, so a solver who hardens the shared data-utils helper can argue React is the library's problem and leave it. They may also not notice that React passes (contentType, data) through a different implementation.",
 "O4_distance": {
  "files": 15,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Raster image blobs (image/png, image/jpeg) must still open inline in a new window as images, and text/plain text blobs must still open as text. A fix that always forces a download, or always forces octet-stream, breaks the image-preview click on list and detail pages.",
  "where": "fix.diff:27-31, fix.diff:39-42, fix.diff:219-224; generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/detail/_entityFile_-detail.html.ejs:52"
 },
 "O6_input_shapes": [
  "content type with parameters (e.g. 'image/png; charset=...'): split on ';' (fix.diff:215)",
  "mixed case and surrounding whitespace: trim().toLowerCase() (fix.diff:215)",
  "XML-based image types via '+xml' suffix (image/svg+xml): forced download even for image blobs (fix.diff:216-218)",
  "null/undefined content type: '' then download (fix.diff:215, 225)",
  "non-plain text types (text/html) on a text blob: download (fix.diff:222-225)",
  "blob kind unspecified ('any' default) for non-image 'open' links: download (fix.diff:214, 228)"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "generators/vue/templates/src/main/webapp/app/shared/data/data-utils.service.ts.ejs:67-76 (setFileData stores file.type, which the client controls, as <field>ContentType; nothing on the server validates it)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "generators/vue/templates/src/main/webapp/app/shared/data/data-utils.service.ts.ejs:83-97",
   "sibling": "downloadFile builds a Blob with the stored contentType. Removing tempLink.download, or a 'preview' variant that opens it with window.open, would be a second unguarded opener.",
   "why_realistic": "It is already a second blob builder that copies the stored type verbatim; a maintainer adding a 'view' action next to 'download' would likely copy it."
  },
  {
   "where": "generators/angular/templates/src/main/webapp/app/core/util/data-util.service.ts.ejs:48-49",
   "sibling": "A service-level 'previewFile' that builds its own Blob/object URL instead of delegating to the shared helper.",
   "why_realistic": "Angular's DataUtils already wraps the shared helper. An inline reimplementation for a preview feature is a plausible copy-paste."
  },
  {
   "where": "generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-update.tsx.ejs:218",
   "sibling": "React update form ValidatedBlobField 'open' link that uses react-jhipster's openFile (or a local copy).",
   "why_realistic": "Angular and Vue update forms have an open link (generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/update/_entityFile_-update.html.ejs:69); React leaves it to the library component."
  }
 ],
 "O9_family": "CWE-79 stored XSS via attacker-controlled MIME type of a same-origin blob: URL (content-type allowlist / sniffing)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript generator emitting EJS templates (Angular/React/Vue TypeScript)",
  "toolchain": "Node.js + npm; esmocha for generator tests (package.json:122); generated-app specs run with vitest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Template spec files: generators/angular/templates/src/main/webapp/app/core/util/data-util.service.spec.ts.ejs, generators/vue/templates/src/main/webapp/app/shared/data/data-utils.service.spec.ts.ejs, Angular entity detail spec. These run only in a generated app (needs npm install). The generator tests themselves are snapshot based."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "client/common shared/jhipster/data-utils.ts.ejs; angular core/util/data-util.service.ts.ejs, entity detail/list/update .ts.ejs and detail/list .html.ejs; react _entityFile_-detail.tsx.ejs, _entityFile_.tsx.ejs; vue _entityFile_-details.vue.ejs, _entityFile_.vue.ejs, shared/data/data-utils.service.ts.ejs",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Block only text/html (or always force octet-stream) inside the shared data-utils openFile, leaving svg+xml/parameterised/case variants open (or breaking image preview) and leaving React on react-jhipster's own openFile."
 },
 "out_of_scope_notes": [
  "The server side accepts and stores any <field>ContentType with no validation; that is a separate server-side hardening question, not pursued.",
  "<img [src]=\"'data:' + ContentType ...\"> renders in list/detail/update views also put the stored type into a data: URL. Inside an img this does not run script, so not pursued."
 ],
 "unverified": [
  "Whether react-jhipster 1.0.3 (generators/react/resources/package.json:15) ValidatedBlobField or its openFile has its own unguarded Blob/window.open: external package, not in this tree.",
  "repo_mb: size not measured (no shell used).",
  "Whether a generated app's vitest specs can run fully offline: depends on a pre-populated npm cache.",
  "Recall risk: fix is recent (2026-10) and narrowly written up; rated low without checking external coverage.",
  "Non-image 'open' links (e.g. generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/list/_entityFile_.html.ejs:133, generators/vue/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-update.vue.ejs:35) are not edited by the fix but are covered by the 'any' default in the shared helper; counted as fixed, not O8."
 ]
}
  ```
- Published fix sites:   - generators/client/generators/common/templates/src/main/webapp/app/shared/jhipster/data-utils.ts.ejs:49-60 — entry point: generated app: openFile(data, contentType) shared helper (all clients), reached by clicking an entity blob/image link [shared client helper template (core sink)]
  - generators/angular/templates/src/main/webapp/app/core/util/data-util.service.ts.ejs:48-49 — entry point: Angular DataUtils.openFile service API [Angular wrapper service]
  - generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/detail/_entityFile_-detail.html.ejs:52 — entry point: Angular entity detail page, image blob click [Angular view template]
  - generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/detail/_entityFile_-detail.ts.ejs:81-82 — entry point: Angular entity detail component openFile [Angular component wrapper]
  - generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/list/_entityFile_.html.ejs:124 — entry point: Angular entity list page, image blob click [Angular view template]
  - generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/list/_entityFile_.ts.ejs:279-280 — entry point: Angular entity list component openFile [Angular component wrapper]
  - generators/angular/templates/src/main/webapp/app/entities/_entityFolder_/update/_entityFile_-update.ts.ejs:177-178 — entry point: Angular entity update component openFile (update form 'open' link) [Angular component wrapper]
  - generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-detail.tsx.ejs:26 — entry point: React entity detail page blob/image click (was react-jhipster openFile) [React view; switches from external library implementation to local helper]
  - generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-detail.tsx.ejs:99 — entry point: React entity detail page blob/image click [React view]
  - generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.tsx.ejs:28 — entry point: React entity list page blob/image click (was react-jhipster openFile) [React view; switches implementation]
  - generators/react/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.tsx.ejs:420 — entry point: React entity list page blob/image click [React view]
  - generators/vue/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_-details.vue.ejs:17 — entry point: Vue entity details page, image blob click [Vue view template]
  - generators/vue/templates/src/main/webapp/app/entities/_entityFolder_/_entityFile_.vue.ejs:70 — entry point: Vue entity list page, image blob click [Vue view template]
  - generators/vue/templates/src/main/webapp/app/shared/data/data-utils.service.ts.ejs:46-47 — entry point: Vue useDataUtils().openFile composable API (argument order reversed: contentType, data) [Vue wrapper composable]
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

## Environment (`tasks/generator-jhipster-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/generator-jhipster-ds/instruction.md`)
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

## Tests (`tasks/generator-jhipster-ds/tests/`)
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
- **Wrong-fix patches** go in `build/generator-jhipster-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/generator-jhipster-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/generator-jhipster-ds/manifest.json`:**
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

**Also in `build/generator-jhipster-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py generator-jhipster-ds --only static
python3 -I builder/gate.py generator-jhipster-ds --only nop
python3 -I builder/gate.py generator-jhipster-ds --only oracle
python3 -I builder/gate.py generator-jhipster-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/generator-jhipster-ds/`;
  - edit only `tasks/generator-jhipster-ds/`, `build/generator-jhipster-ds/` and, for pattern B, the register;
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
