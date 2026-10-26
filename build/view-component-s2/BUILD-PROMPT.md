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

Project root: `/home/mara/cwe-bench`. Task: `view-component-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-9H85-G7W3-RH49", "CVE-2026-54497"]; viewcomponent/view_component; cross-request/session data exposure through mutable instance state retained on a reused object (CWE-362 race on shared state, CWE-488 exposure to the wrong session, CWE-668 exposure to the wrong sphere)
- Pinned (vulnerable) commit: 48e5fd2d602344c7d33019fbc5c8b087e315bb78. Published fix: 7b05073be28037f7d5ff141e9dd42f3cf47956a4.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "29635",
 "advisory_ids": [
  "GHSA-9H85-G7W3-RH49",
  "CVE-2026-54497"
 ],
 "repo": "viewcomponent/view_component",
 "pinned_commit": "48e5fd2d602344c7d33019fbc5c8b087e315bb78",
 "fix_commits": [
  "7b05073be28037f7d5ff141e9dd42f3cf47956a4"
 ],
 "trust_decision": {
  "summary": "A component instance is single-use: at the render boundary (`ViewComponent::Base#render_in`) every view-context-derived ivar is refreshed on each call and a second render raises `ViewComponent::ReusedInstanceError` (configurable to warn only).",
  "evidence": [
   "lib/view_component/base.rb:111-124",
   "fix.diff:22-48",
   "fix.diff:64-95",
   "fix.diff:150-158"
  ]
 },
 "landing_point": {
  "where": "lib/view_component/base.rb:111-124",
  "why": "An engineer reading \"reused component instances retain stale render context\" looks first at #render_in, where @__vc_original_view_context, @lookup_context, @view_flow and @__vc_requested_details are memoized with `||=` and where @__vc_controller/@__vc_helpers/@__vc_request are first derived."
 },
 "fix_sites": [
  {
   "where": "lib/view_component/base.rb:111-124",
   "entry_point": "ViewComponent::Base#render_in (ActionView `render component` / `render_inline` / slot rendering)",
   "module_kind": "core component base class"
  },
  {
   "where": "fix.diff:64-95",
   "entry_point": "ViewComponent::Base#render_in (`__vc_check_reused_instance!` / `__vc_reset_render_state!`)",
   "module_kind": "core component base class, new guard helpers"
  },
  {
   "where": "lib/view_component/collection.rb:36-48",
   "entry_point": "ViewComponent::Collection#render_in (`Model.with_collection` / rendering a collection)",
   "module_kind": "collection renderer"
  },
  {
   "where": "lib/view_component/collection.rb:73-79",
   "entry_point": "ViewComponent::Collection#render_in with a caller-supplied `spacer_component:`",
   "module_kind": "collection renderer, spacer path"
  },
  {
   "where": "fix.diff:150-158",
   "entry_point": "Rails initializer `config.view_component.raise_on_reused_instances`",
   "module_kind": "configuration defaults"
  },
  {
   "where": "fix.diff:184-197",
   "entry_point": "ViewComponent::Base#render_in (raise path)",
   "module_kind": "errors"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "lib/view_component/collection.rb:36-48"
 },
 "O3_reason_to_dismiss": "A Collection is built from the collection argument and is not \"a component instance\"; its memoized @components reads as a performance cache and the spacer as caller-supplied configuration, so the reuse in Collection#render_in looks like framework plumbing the advisory is not about.",
 "O4_distance": {
  "files": 2,
  "packages": 0,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Content and slots set by the caller before render (`with_content`, `with_*_slot`) share the instance-variable namespace with the render-scoped ivars; a reset that clears every ivar (or dup-ing the instance) drops them and the component renders without its caller-supplied content - the published fix deliberately preserves @__vc_set_slots and @__vc_content_set_by_with_content.",
  "where": "lib/view_component/with_content_helper.rb:8, lib/view_component/slotable.rb:434-441"
 },
 "O6_input_shapes": [
  "the same component instance rendered a second time through #render_in",
  "the same instance aliased into two positions of one parent (inline items array)",
  "the same Collection object rendered twice (children rebuilt per render)",
  "a Collection with a caller-supplied spacer_component rendered twice (spacer dup'd before render)",
  "guard disabled via config (`raise_on_reused_instances = false`): warning instead of raise, state still refreshed"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "lib/view_component/config.rb:13-19",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "Slot#to_s caches its rendered HTML in @content and never invalidates it; slot objects live in @__vc_set_slots, which the fix deliberately preserves, so a second render of the same instance replays the previous render's slot output and the child component's new guard never fires because render_in is not called again",
   "where": "lib/view_component/slot.rb:45-79",
   "reason_to_dismiss": "Slot state is the thing the fix explicitly declares caller-owned and preserved, so its cached HTML looks like caller data rather than render context",
   "distance": "1 file from the landing point (lib/view_component/slot.rb), same gem package; the advisory never mentions slots",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Public accessors #controller, #helpers, #request (and the delegates onto helpers: output_buffer, lookup_context, view_flow) keep answering from the previous render's view context after the render ends: render_in's ensure restores only @virtual_path and @current_template, and @view_context plus @__vc_controller/@__vc_helpers/@__vc_request are cleared only at the start of the next render, so a retained instance exposes the old request with no second render for the guard to catch",
   "where": "lib/view_component/base.rb:313-334",
   "reason_to_dismiss": "The accessors are documented as valid inside a render and no reuse happens on this route, so it looks outside the advisory's \"rendered a second time\" framing",
   "distance": "same file as the landing point, ~200 lines below it",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/view_component/slot.rb:45-79",
   "sibling": "a per-render invalidation of a Slot's cached @content, mirroring __vc_reset_render_state!",
   "why_realistic": "slots hold child component instances and rendered HTML produced during a render, so the same reset a maintainer wrote for the component is a natural thing to write for the slot wrapper"
  },
  {
   "where": "lib/view_component/collection.rb:73-79",
   "sibling": "a second retained-instance path beside the spacer (a memoized per-item wrapper or an options/iterator object the collection keeps)",
   "why_realistic": "Collection already holds instances long-term and the fix had to special-case the spacer, so another retention path next to it is a plausible follow-on feature"
  },
  {
   "where": "lib/view_component/slotable.rb:355-360",
   "sibling": "caching the default-method slot (which today is rebuilt on each call) in @__vc_set_slots",
   "why_realistic": "caching a slot built by a default method is an obvious performance change and would recreate exactly the stale-state mechanism the advisory is about"
  }
 ],
 "O9_family": "cross-request/session data exposure through mutable instance state retained on a reused object (CWE-362 race on shared state, CWE-488 exposure to the wrong session, CWE-668 exposure to the wrong sphere)",
 "O9_dos": false,
 "O10_build": {
  "language": "Ruby",
  "toolchain": "Ruby 4.0 + bundler + rake + appraisal (Gemfile, gemfiles/rails_*.gemfile); Rails 8.1 by default, native gems (nokogiri) compiled at install",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Minitest under test/sandbox/test (rendering_test.rb, collection_test.rb, slot_test.rb); `bundle exec rake test` / `rake all_tests`"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "lib/view_component/base.rb, lib/view_component/collection.rb, lib/view_component/config.rb, lib/view_component/errors.rb",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace the `||=` memoization in Base#render_in with plain assignment (refresh controller/helpers/request/lookup_context/view_flow) and stop there, leaving Collection, the spacer and slot content untouched"
 },
 "out_of_scope_notes": [],
 "unverified": [
  "repo size in MB could not be measured without shell access (no du/stat); tiny_repo not evaluated",
  "present_in_latest is unknown for both O8 routes because no latest release was supplied for this screen",
  "j_defence_ineffective=1 is based on the pre-render guards at lib/view_component/base.rb:314 and :324, which do not cover reuse across renders",
  "whether the hidden tests exercise the guard-disabled warning path could not be checked; the fix's own test file relies on a capture_warnings helper whose definition was not traced"
 ]
}
  ```
- Published fix sites:   - lib/view_component/base.rb:111-124 — entry point: ViewComponent::Base#render_in (ActionView `render component` / `render_inline` / slot rendering) [core component base class]
  - fix.diff:64-95 — entry point: ViewComponent::Base#render_in (`__vc_check_reused_instance!` / `__vc_reset_render_state!`) [core component base class, new guard helpers]
  - lib/view_component/collection.rb:36-48 — entry point: ViewComponent::Collection#render_in (`Model.with_collection` / rendering a collection) [collection renderer]
  - lib/view_component/collection.rb:73-79 — entry point: ViewComponent::Collection#render_in with a caller-supplied `spacer_component:` [collection renderer, spacer path]
  - fix.diff:150-158 — entry point: Rails initializer `config.view_component.raise_on_reused_instances` [configuration defaults]
  - fix.diff:184-197 — entry point: ViewComponent::Base#render_in (raise path) [errors]
- Uncovered routes to confirm (pattern B):   - lib/view_component/slot.rb:45-79 — Slot#to_s caches its rendered HTML in @content and never invalidates it; slot objects live in @__vc_set_slots, which the fix deliberately preserves, so a second render of the same instance replays the previous render's slot output and the child component's new guard never fires because render_in is not called again (reason to dismiss: Slot state is the thing the fix explicitly declares caller-owned and preserved, so its cached HTML looks like caller data rather than render context; still in latest: unknown)
  - lib/view_component/base.rb:313-334 — Public accessors #controller, #helpers, #request (and the delegates onto helpers: output_buffer, lookup_context, view_flow) keep answering from the previous render's view context after the render ends: render_in's ensure restores only @virtual_path and @current_template, and @view_context plus @__vc_controller/@__vc_helpers/@__vc_request are cleared only at the start of the next render, so a retained instance exposes the old request with no second render for the guard to catch (reason to dismiss: The accessors are documented as valid inside a render and no reuse happens on this route, so it looks outside the advisory's "rendered a second time" framing; still in latest: unknown)
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

## Environment (`tasks/view-component-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/view-component-s2/instruction.md`)
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

## Tests (`tasks/view-component-s2/tests/`)
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
- **Wrong-fix patches** go in `build/view-component-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/view-component-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/view-component-s2/manifest.json`:**
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

**Also in `build/view-component-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py view-component-s2 --only static
python3 -I common/gate/gate.py view-component-s2 --only nop
python3 -I common/gate/gate.py view-component-s2 --only oracle
python3 -I common/gate/gate.py view-component-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/view-component-s2/`;
  - edit only `tasks/view-component-s2/`, `build/view-component-s2/` and, for pattern B, the register;
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
