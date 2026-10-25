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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-angular`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-HH8M-FM6V-7CVG", "CVE-2026-88057"]; angular/angular; XSS / sanitization bypass (CWE-79): context-dependent sanitizer chosen from the declared selector instead of the concrete element
- Pinned (vulnerable) commit: parent of 2f96c8020f85ccb715a76de4b79a0c680c2c7264 (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/11823/repo). Published fix: 2f96c8020f85ccb715a76de4b79a0c680c2c7264, 6afe6fa781c2f0931f0aedd729b9884a8fe212ee, 6caa298dee58319b2d674dc91364e26ffe3ecb2b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "11823",
 "advisory_ids": [
  "GHSA-HH8M-FM6V-7CVG",
  "CVE-2026-88057"
 ],
 "repo": "angular/angular",
 "pinned_commit": "parent of 2f96c8020f85ccb715a76de4b79a0c680c2c7264 (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/11823/repo)",
 "fix_commits": [
  "2f96c8020f85ccb715a76de4b79a0c680c2c7264",
  "6afe6fa781c2f0931f0aedd729b9884a8fe212ee",
  "6caa298dee58319b2d674dc91364e26ffe3ecb2b"
 ],
 "trust_decision": {
  "summary": "Which sanitizer guards a directive host binding is decided at compile time from the declaring directive's selector, not the element the directive actually lands on (compiler ingest/binding_parser). At runtime it is decided from tNode.value, which is the literal '#host' for dynamically created root hosts, plus hand-copied tag tables in core sanitization.ts. So a selector that names a harmless or custom element can carry srcdoc/src/data/sandbox bindings onto an iframe/object/SVG/MathML host without the right sanitizer.",
  "evidence": [
   "packages/compiler/src/template/pipeline/src/ingest.ts:122-134",
   "packages/compiler/src/template_parser/binding_parser.ts:899-939",
   "packages/compiler/src/template/pipeline/src/phases/resolve_sanitizers.ts:61-74",
   "packages/core/src/render3/component_ref.ts:326-334",
   "packages/core/src/sanitization/sanitization.ts:217-239",
   "packages/core/src/sanitization/sanitization.ts:318-338",
   "packages/core/src/render3/instructions/shared.ts:304",
   "packages/core/src/render3/instructions/shared.ts:531"
  ]
 },
 "landing_point": {
  "where": "packages/compiler/src/template/pipeline/src/ingest.ts:122",
  "why": "The summary says 'directive host bindings' and '@angular/compiler'. ingestHostBinding is where the host-binding security context is computed from input.componentSelector."
 },
 "fix_sites": [
  {
   "where": "packages/compiler/src/template/pipeline/src/ingest.ts:122-134",
   "entry_point": "@Directive/@Component host: {'[attr.x]'/'[x]'} compiled by ngtsc, JIT or the partial linker (all via compileDirectiveFromMetadata -> packages/compiler/src/render3/view/compiler.ts:515)",
   "module_kind": "compiler: host-binding ingestion"
  },
  {
   "where": "packages/compiler/src/template/pipeline/src/phases/resolve_sanitizers.ts:61-101",
   "entry_point": "same compile path; picks the sanitizer instruction from the security-context set",
   "module_kind": "compiler: pipeline phase"
  },
  {
   "where": "packages/compiler/src/schema/dom_element_schema_registry.ts:445-452",
   "entry_point": "same compile path; also template bindings and i18n attribute bindings on SVG/MathML elements",
   "module_kind": "compiler: schema registry"
  },
  {
   "where": "packages/compiler/src/schema/dom_security_schema.ts:154-168",
   "entry_point": "schema table consumed by every compile-time security lookup (adds MathML '*' href and a namespaced wildcard)",
   "module_kind": "compiler: schema data"
  },
  {
   "where": "packages/core/src/sanitization/dom_security_schema.ts:71-107",
   "entry_point": "runtime copy of the schema, used by the i18n runtime and (after the fix) the runtime sanitizers",
   "module_kind": "core: second copy of the schema"
  },
  {
   "where": "packages/core/src/sanitization/sanitization.ts:49-58",
   "entry_point": "\u0275\u0275sanitizeHtml codegen API, called from \u0275\u0275domProperty/\u0275\u0275attribute with (value, tNode.value, name)",
   "module_kind": "core: runtime sanitizer"
  },
  {
   "where": "packages/core/src/sanitization/sanitization.ts:217-258",
   "entry_point": "\u0275\u0275sanitizeUrlOrResourceUrl codegen API (host-binding href/src/data/action/codebase)",
   "module_kind": "core: runtime sanitizer (hand-copied RESOURCE_MAP)"
  },
  {
   "where": "packages/core/src/sanitization/sanitization.ts:318-391",
   "entry_point": "\u0275\u0275validateAttribute codegen API (iframe sandbox/allow..., SVG animate attributeName)",
   "module_kind": "core: runtime validator (hand-copied SECURITY_SENSITIVE_ELEMENTS)"
  },
  {
   "where": "packages/core/src/render3/component_ref.ts:330",
   "entry_point": "createComponent(Cmp, {hostElement, directives}) / ViewContainerRef.createComponent(Cmp, {directives}); root host TNode named '#host'",
   "module_kind": "core: dynamic component creation"
  },
  {
   "where": "packages/core/src/render3/i18n/i18n_parse.ts:818-824",
   "entry_point": "i18n ICU content containing elements with bound/static attributes (walkIcuTree)",
   "module_kind": "core: i18n runtime (second sanitizer-resolution implementation)"
  },
  {
   "where": "packages/core/src/render3/i18n/i18n_parse.ts:1013-1020",
   "entry_point": "i18n attribute bindings (packages/core/src/render3/i18n/i18n_parse.ts:389-398) and ICU attributes",
   "module_kind": "core: i18n runtime sanitizer resolver"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "packages/core/src/sanitization/sanitization.ts:217-239 (runtime RESOURCE_MAP hand copy) and packages/core/src/render3/i18n/i18n_parse.ts:1013-1020 (i18n runtime's own schema lookup, missing the namespaced wildcard)"
 },
 "O3_reason_to_dismiss": "The advisory blames the compiler choosing the sanitizer from the selector. A solver can argue the runtime tables and the i18n resolver are a separate legacy/i18n feature, since host bindings cannot carry i18n, and that the runtime 'already sanitizes'. But '#host' dynamic roots and MathML '*' href only close in core.",
 "O4_distance": {
  "files": 11,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Host bindings of srcdoc/data/action/href on non-sensitive concrete hosts must keep their raw value: div[attr.data]='javascript:...', div srcdoc, div action, svg rect href. Selector-specific output, such as innerHTML->sanitizeHtml, must also stay unchanged. Sanitizing every candidate context everywhere, or keeping getUrlSanitizer's 'default to URL sanitizer', breaks these.",
  "where": "packages/core/src/sanitization/sanitization.ts:235-239; fix.diff:1168-1201; fix.diff:1290-1312; fix.diff:1583-1588; fix.diff:1646"
 },
 "O6_input_shapes": [
  "attribute binding [attr.x] vs DOM property binding [x] (\u0275\u0275attribute vs \u0275\u0275domProperty)",
  "HTML vs SVG vs MathML namespace hosts (createElementNS), including MathML '*' href/xlink:href",
  "xlink:href vs href",
  "dynamic root host named '#host' (createComponent hostElement / ViewContainerRef.createComponent with directives)",
  "directive applied directly, via hostDirectives, and via class inheritance",
  "pure :not(iframe) selectors",
  "case variants of attributeName (getAttributeNames scan)",
  "contexts URL, RESOURCE_URL, HTML, ATTRIBUTE_NO_BINDING, and mixed with NONE"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "packages/core/src/sanitization/dom_security_schema.ts:49-152 (runtime SECURITY_SCHEMA); at the pinned commit runtime checks use hand copies at packages/core/src/sanitization/sanitization.ts:217-226 and packages/core/src/sanitization/sanitization.ts:288-309",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "packages/core/src/sanitization/sanitization.ts:318-338",
   "sibling": "Resolve the '#host' concrete tag only in getUrlSanitizer and leave \u0275\u0275validateAttribute keyed on the raw tag name, so iframe sandbox/allow host bindings on a dynamic iframe host pass",
   "why_realistic": "Pinned code already keeps a separate hand-copied table per sanitizer (RESOURCE_MAP vs SECURITY_SENSITIVE_ELEMENTS). A maintainer fixing one would plausibly miss the other."
  },
  {
   "where": "packages/core/src/render3/i18n/i18n_parse.ts:1013-1020",
   "sibling": "Keep the i18n resolver's own non-namespaced-wildcard lookup, so a MathML element's href in i18n/ICU attributes gets no URL sanitizer",
   "why_realistic": "It is a third independent schema lookup in a different subsystem (i18n), and the fix had to patch it separately."
  },
  {
   "where": "packages/compiler/src/template/pipeline/src/phases/resolve_sanitizers.ts:40-52",
   "sibling": "Host static attributes skip trusted-value/context resolution ('TODO: Is the TDB behavior correct here?'); a sibling could let a host attribute expression reach a sensitive concrete host unchecked",
   "why_realistic": "An existing TODO marks host jobs as deliberately skipped there."
  }
 ],
 "O9_family": "XSS / sanitization bypass (CWE-79): context-dependent sanitizer chosen from the declared selector instead of the concrete element",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Bazel via bazelisk + pnpm 10.18.3 (package.json:9,23)",
  "services": [],
  "offline_after_build": null,
  "project_tests": "packages/core/test/acceptance/security_spec.ts, packages/core/test/sanitization/sanitization_spec.ts, packages/compiler-cli/test/ngtsc/ngtsc_spec.ts, packages/compiler-cli/test/compliance/test_cases/r3_view_compiler_bindings/host_bindings/sanitization.ts"
 },
 "O11_fix_minutes": 150,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/compiler/src/template/pipeline/src/ingest.ts, packages/compiler/src/template/pipeline/src/phases/resolve_sanitizers.ts, packages/compiler/src/schema/dom_element_schema_registry.ts, packages/compiler/src/schema/dom_security_schema.ts, packages/core/src/sanitization/dom_security_schema.ts, packages/core/src/sanitization/sanitization.ts, packages/core/src/render3/component_ref.ts, packages/core/src/render3/i18n/i18n_parse.ts, packages/core/src/render3/interfaces/node.ts, packages/core/src/render3/namespaces.ts, packages/core/src/render3/state.ts (import only), packages/core/src/render3/util/tags.ts (new)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "In ingest.ts, compute host-binding contexts over all known elements (ignore the selector) and emit the strongest sanitizer. This over-sanitizes div data/srcdoc/action, or hits the 'Ambiguous security context' assertion, and leaves the runtime '#host' and MathML lookups unfixed."
 },
 "out_of_scope_notes": [
  "Renderer2.setAttribute/setProperty are unsanitized by design; not pursued.",
  "Compiler-side i18n attribute sanitizer phase (packages/compiler/src/template/pipeline/src/phases/resolve_i18n_attr_sanitizers.ts) uses the schema registry and is covered transitively by the registry change; not examined further."
 ],
 "unverified": [
  "pinned_commit hash: candidate parent_commit is null; the pinned tree was read directly.",
  "O1=3 groups the entry points as: (1) compiled directive/component host bindings on template elements, including hostDirectives and inheritance; (2) dynamic root hosts via createComponent/ViewContainerRef.createComponent ('#host'); (3) i18n/ICU attribute bindings on namespaced elements. This grouping is a judgement call.",
  "O8 is empty because I found no unfixed route to the host-binding sanitizer choice in the routes I enumerated (\u0275\u0275domProperty/\u0275\u0275attribute via shared.ts:304/531, i18n_parse, compiler ingest). Third-party renderers and SSR were not checked.",
  "O4 repo_mb unknown: size not measured (no shell use). giant_repo/tiny_repo not assessed; Angular is unlikely to be under 5 MB but could approach 1.5 GB with history.",
  "O10 offline_after_build unknown: Bazel fetches toolchains/browsers on the first build; acceptance tests may run under headless Chromium web_test targets.",
  "O11=150 min exceeds the 45-minute fairness target; the published fix is large (compiler + core + i18n).",
  "O13 recall_risk: advisory published 2026-09-10, after the model's knowledge cutoff; Angular advisories are usually widely covered, so set to medium."
 ]
}
  ```
- Published fix sites:   - packages/compiler/src/template/pipeline/src/ingest.ts:122-134 — entry point: @Directive/@Component host: {'[attr.x]'/'[x]'} compiled by ngtsc, JIT or the partial linker (all via compileDirectiveFromMetadata -> packages/compiler/src/render3/view/compiler.ts:515) [compiler: host-binding ingestion]
  - packages/compiler/src/template/pipeline/src/phases/resolve_sanitizers.ts:61-101 — entry point: same compile path; picks the sanitizer instruction from the security-context set [compiler: pipeline phase]
  - packages/compiler/src/schema/dom_element_schema_registry.ts:445-452 — entry point: same compile path; also template bindings and i18n attribute bindings on SVG/MathML elements [compiler: schema registry]
  - packages/compiler/src/schema/dom_security_schema.ts:154-168 — entry point: schema table consumed by every compile-time security lookup (adds MathML '*' href and a namespaced wildcard) [compiler: schema data]
  - packages/core/src/sanitization/dom_security_schema.ts:71-107 — entry point: runtime copy of the schema, used by the i18n runtime and (after the fix) the runtime sanitizers [core: second copy of the schema]
  - packages/core/src/sanitization/sanitization.ts:49-58 — entry point: ɵɵsanitizeHtml codegen API, called from ɵɵdomProperty/ɵɵattribute with (value, tNode.value, name) [core: runtime sanitizer]
  - packages/core/src/sanitization/sanitization.ts:217-258 — entry point: ɵɵsanitizeUrlOrResourceUrl codegen API (host-binding href/src/data/action/codebase) [core: runtime sanitizer (hand-copied RESOURCE_MAP)]
  - packages/core/src/sanitization/sanitization.ts:318-391 — entry point: ɵɵvalidateAttribute codegen API (iframe sandbox/allow..., SVG animate attributeName) [core: runtime validator (hand-copied SECURITY_SENSITIVE_ELEMENTS)]
  - packages/core/src/render3/component_ref.ts:330 — entry point: createComponent(Cmp, {hostElement, directives}) / ViewContainerRef.createComponent(Cmp, {directives}); root host TNode named '#host' [core: dynamic component creation]
  - packages/core/src/render3/i18n/i18n_parse.ts:818-824 — entry point: i18n ICU content containing elements with bound/static attributes (walkIcuTree) [core: i18n runtime (second sanitizer-resolution implementation)]
  - packages/core/src/render3/i18n/i18n_parse.ts:1013-1020 — entry point: i18n attribute bindings (packages/core/src/render3/i18n/i18n_parse.ts:389-398) and ICU attributes [core: i18n runtime sanitizer resolver]
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
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-angular/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-angular/instruction.md`)
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

## Tests (`tasks/pv-angular/tests/`)
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
- **Wrong-fix patches** go in `build/pv-angular/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-angular/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-angular/manifest.json`:**
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

**Also in `build/pv-angular/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-angular --only static
python3 -I builder/gate.py pv-angular --only nop
python3 -I builder/gate.py pv-angular --only oracle
python3 -I builder/gate.py pv-angular --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-angular/`;
  - edit only `tasks/pv-angular/`, `build/pv-angular/` and, for pattern B, the register;
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
