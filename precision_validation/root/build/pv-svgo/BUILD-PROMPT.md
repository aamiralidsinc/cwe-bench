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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-svgo`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-4VPR-X523-8J87", "CVE-2026-84369"]; svg/svgo; XSS / incomplete HTML-SVG sanitisation (CWE-79), denylist-based
- Pinned (vulnerable) commit: unknown (parent of 0557385564a5c6c11d76cd934a6cff94451e532c; parent_commit field is null; tree is svgo 3.3.4 per package.json:4). Published fix: 0557385564a5c6c11d76cd934a6cff94451e532c, 994a9f00d79ddec68ce19a1ce9eb8ca08d747e4f, fd51e474a300417d9361d9302d596b1763146327.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8441",
 "advisory_ids": [
  "GHSA-4VPR-X523-8J87",
  "CVE-2026-84369"
 ],
 "repo": "svg/svgo",
 "pinned_commit": "unknown (parent of 0557385564a5c6c11d76cd934a6cff94451e532c; parent_commit field is null; tree is svgo 3.3.4 per package.json:4)",
 "fix_commits": [
  "0557385564a5c6c11d76cd934a6cff94451e532c",
  "994a9f00d79ddec68ce19a1ce9eb8ca08d747e4f",
  "fd51e474a300417d9361d9302d596b1763146327"
 ],
 "trust_decision": {
  "summary": "The removeScriptElement plugin decides which elements/attributes of untrusted SVG count as executable and strips them. At the pinned commit it only checks a fixed SVG event-attribute list and `javascript:` hrefs on <a>, and does nothing for HTML inside <foreignObject>.",
  "evidence": [
   "plugins/removeScriptElement.js:83-94",
   "plugins/removeScriptElement.js:106-133",
   "lib/svgo/tools.js:160-171"
  ]
 },
 "landing_point": {
  "where": "plugins/removeScriptElement.js:90-94",
  "why": "The advisory names removeScripts and foreignObject event/HTML attributes; the event-attribute deletion loop in the plugin is the obvious first place to look."
 },
 "fix_sites": [
  {
   "where": "plugins/removeScriptElement.js:90-94",
   "entry_point": "optimize(svg, {plugins:['removeScriptElement']}) (lib/svgo.js:50, lib/svgo-node.js:69) and CLI `svgo` (lib/svgo/coa.js:392)",
   "module_kind": "plugin (attribute stripping on enter): adds foreignObject depth tracking, on*/srcdoc/executable-URL removal"
  },
  {
   "where": "plugins/removeScriptElement.js:106-133",
   "entry_point": "same as above",
   "module_kind": "plugin (anchor collapse on exit): namespace-aware <a> plus isExecutableUrl instead of javascript: prefix"
  },
  {
   "where": "lib/svgo/tools.js:155-182",
   "entry_point": "exported helper hasScripts, used by cleanupIds (plugins/cleanupIds.js:159), minifyStyles (plugins/minifyStyles.js:64), removeHiddenElems (plugins/removeHiddenElems.js:147), removeUselessStrokeAndFill (plugins/removeUselessStrokeAndFill.js:30), all in preset-default",
   "module_kind": "shared tools module: second copy of the javascript: href check, plus the new isExecutableUrl helper (fix.diff:24-72)"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "lib/svgo/tools.js:160-171 (hasScripts duplicates the `javascript:` href test; fix.diff:80-92 switches it to isExecutableUrl)"
 },
 "O3_reason_to_dismiss": "hasScripts only decides whether other optimisation plugins hold back on script-bearing nodes; it removes nothing, so a solver can argue it is not part of the removeScripts sanitiser. For O8, the plugin docs scope event removal to 'SVG event attributes' (docs/03-plugins/remove-scripts.mdx:20), and XML is case-sensitive, so an uppercase or unlisted event name looks like a non-issue.",
 "O4_distance": {
  "files": 2,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Visual foreignObject HTML must survive: elements, style, class, title and non-executable src stay; data:image/png anchors stay uncollapsed; <a>/<foreignObject>/srcdoc in unrelated namespaces stay. An over-broad fix that drops all foreignObject content, all data: URLs or all on*/href attributes breaks these.",
  "where": "fix.diff:290-305 (PNG data anchor kept), fix.diff:321-355 (iframe src kept, custom:foreignObject srcdoc kept), fix.diff:384-399 (custom:a kept)"
 },
 "O6_input_shapes": [
  "unlisted HTML on* attributes inside foreignObject (e.g. onbeforetoggle), any prefix, case-insensitive (fix.diff:177-180)",
  "srcdoc inside foreignObject (fix.diff:181-182)",
  "action/data/formaction/href/src holding executable URLs inside foreignObject (fix.diff:140, fix.diff:183-186)",
  "data: URLs with text/html, application/xhtml+xml or image/svg+xml media types, with/without ;params, case-insensitive (fix.diff:55-70)",
  "vbscript: scheme (fix.diff:48-53)",
  "tab/CR/LF embedded in the scheme name (fix.diff:37-42)",
  "namespace-prefixed SVG <a> and <foreignObject> (svg:a, locally declared alias:a) (fix.diff:156-165, fix.diff:194-205)",
  "prefixed href (xlink:href or any *:href) on <a> (fix.diff:241)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "Event attributes on SVG elements outside foreignObject that are missing from the fixed list (e.g. onpointerdown, onanimationstart, onwheel, onauxclick, onbeforetoggle) are still kept, because outside foreignObject the check is exact membership in eventAttrs.",
   "where": "plugins/removeScriptElement.js:10-16",
   "reason_to_dismiss": "The docs promise removal of 'SVG event attributes' (docs/03-plugins/remove-scripts.mdx:20) and the list is taken from the SVG 1.1 attribute groups (plugins/_collections.js:152-163, 238-304); HTML-only events look like a neighbouring feature.",
   "distance": "same file as the landing point; list lives in plugins/_collections.js",
   "present_in_latest": "yes",
   "latest_where": "latest/plugins/removeScripts.js:113"
  },
  {
   "route": "Mixed-case event attribute names outside foreignObject (e.g. onLoad) skip the exact-case check; HTML parsers lowercase them when the SVG is inlined in HTML.",
   "where": "plugins/removeScriptElement.js:90-94",
   "reason_to_dismiss": "SVG is XML and case-sensitive, so a solver can argue onLoad is not an event attribute in a standalone .svg.",
   "distance": "same file as the landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/plugins/removeScripts.js:112-114"
  },
  {
   "route": "Mixed-case script element names (e.g. SCRIPT inside foreignObject HTML) are not matched, because the element name test is exact-case.",
   "where": "plugins/removeScriptElement.js:31-35",
   "reason_to_dismiss": "Element names are case-sensitive in XML; the advisory is about attributes, not about <script>, which already 'works'.",
   "distance": "same file as the landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/plugins/removeScripts.js:38-41"
  },
  {
   "route": "SVG animation elements (<set>/<animate> with attributeName=href and to/values holding a javascript: URL) can retarget an <a> href, and the plugin never checks to/values/from.",
   "where": "plugins/removeScriptElement.js:96-133",
   "reason_to_dismiss": "Animation is a separate SVG feature and the anchor check is written against static href attributes only; browser support for this route is unclear.",
   "distance": "same file; animation attrs defined in plugins/_collections.js:137-145",
   "present_in_latest": "yes",
   "latest_where": "latest/plugins/removeScripts.js:150-167"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/svgo/tools.js:173-181",
   "sibling": "hasScripts recomputes its own event list and does not know about foreignObject HTML on*/srcdoc; a sibling helper with a private javascript:-only check would be realistic.",
   "why_realistic": "The pinned tree already duplicates the javascript: check in two files (lib/svgo/tools.js:165, plugins/removeScriptElement.js:114-117), so a third copy elsewhere is in keeping with how the code is written."
  },
  {
   "where": "plugins/removeScriptElement.js:106-133",
   "sibling": "Collapse or strip executable hrefs on other SVG navigation/load elements (e.g. an xlink:href check limited to <a>, with a parallel element added in our copy), sharing a private prefix test instead of isExecutableUrl.",
   "why_realistic": "The anchor branch is a hand-rolled per-element check; adding a second element with its own inline check is a natural maintainer change."
  }
 ],
 "O9_family": "XSS / incomplete HTML-SVG sanitisation (CWE-79), denylist-based",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (Node.js, CommonJS)",
  "toolchain": "Node >=14 (package.json:62-64), yarn 2.4.3 (package.json:2), jest (package.json:66)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Fixture-driven plugin tests test/plugins/removeScriptElement.01-08.svg run by test/plugins/_index.test.js; fix adds .09-.11 (fix.diff:269-400)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "plugins/removeScriptElement.js, lib/svgo/tools.js",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Strip all on* attributes inside foreignObject in removeScriptElement.js and leave the javascript:-only anchor checks in the plugin and in tools.js hasScripts as they are."
 },
 "out_of_scope_notes": [
  "isNamespaceAwareElem dereferences prefixes.get(prefix) without a guard for undeclared prefixes (plugins/removeScriptElement.js:40-41); this is a crash risk, not this protection.",
  "Plugin is disabled by default and not in preset-default (plugins/removeScriptElement.js:7), so the sink is reached only when it is explicitly enabled.",
  "Latest upstream renamed the plugin to removeScripts and moved to ESM (latest/plugins/removeScripts.js:5)."
 ],
 "unverified": [
  "repo_mb not measured (no shell); about 75 JS files under lib/plugins/bin, so tiny_repo (<5 MB source) is inferred, not measured.",
  "Pinned commit hash not given (parent_commit null); assumed to be the parent of the first fix commit.",
  "Whether current browsers still execute javascript: hrefs set by SVG <set>/<animate> (O8 route 4) was not checked.",
  "Executability of mixed-case event/script names depends on the SVG being inlined in an HTML document; not exercised.",
  "Docs say 'Removes all scripts from the document.' (docs/03-plugins/remove-scripts.mdx:7) but then list scoped operations (lines 19-21); not flagged as protection_documented_without_exceptions.",
  "Whether the three fix commits each touch source, or only tests/docs, was not split; fix.diff shows the combined change.",
  "Recall risk is a judgement: svgo is widely used, but the advisory is recent (2026-09-08)."
 ]
}
  ```
- Published fix sites:   - plugins/removeScriptElement.js:90-94 — entry point: optimize(svg, {plugins:['removeScriptElement']}) (lib/svgo.js:50, lib/svgo-node.js:69) and CLI `svgo` (lib/svgo/coa.js:392) [plugin (attribute stripping on enter): adds foreignObject depth tracking, on*/srcdoc/executable-URL removal]
  - plugins/removeScriptElement.js:106-133 — entry point: same as above [plugin (anchor collapse on exit): namespace-aware <a> plus isExecutableUrl instead of javascript: prefix]
  - lib/svgo/tools.js:155-182 — entry point: exported helper hasScripts, used by cleanupIds (plugins/cleanupIds.js:159), minifyStyles (plugins/minifyStyles.js:64), removeHiddenElems (plugins/removeHiddenElems.js:147), removeUselessStrokeAndFill (plugins/removeUselessStrokeAndFill.js:30), all in preset-default [shared tools module: second copy of the javascript: href check, plus the new isExecutableUrl helper (fix.diff:24-72)]
- Uncovered routes to confirm (pattern B):   - plugins/removeScriptElement.js:10-16 — Event attributes on SVG elements outside foreignObject that are missing from the fixed list (e.g. onpointerdown, onanimationstart, onwheel, onauxclick, onbeforetoggle) are still kept, because outside foreignObject the check is exact membership in eventAttrs. (reason to dismiss: The docs promise removal of 'SVG event attributes' (docs/03-plugins/remove-scripts.mdx:20) and the list is taken from the SVG 1.1 attribute groups (plugins/_collections.js:152-163, 238-304); HTML-only events look like a neighbouring feature.; still in latest: yes)
  - plugins/removeScriptElement.js:90-94 — Mixed-case event attribute names outside foreignObject (e.g. onLoad) skip the exact-case check; HTML parsers lowercase them when the SVG is inlined in HTML. (reason to dismiss: SVG is XML and case-sensitive, so a solver can argue onLoad is not an event attribute in a standalone .svg.; still in latest: yes)
  - plugins/removeScriptElement.js:31-35 — Mixed-case script element names (e.g. SCRIPT inside foreignObject HTML) are not matched, because the element name test is exact-case. (reason to dismiss: Element names are case-sensitive in XML; the advisory is about attributes, not about <script>, which already 'works'.; still in latest: yes)
  - plugins/removeScriptElement.js:96-133 — SVG animation elements (<set>/<animate> with attributeName=href and to/values holding a javascript: URL) can retarget an <a> href, and the plugin never checks to/values/from. (reason to dismiss: Animation is a separate SVG feature and the anchor check is written against static href attributes only; browser support for this route is unclear.; still in latest: yes)
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

## Environment (`tasks/pv-svgo/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-svgo/instruction.md`)
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

## Tests (`tasks/pv-svgo/tests/`)
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
- **Wrong-fix patches** go in `build/pv-svgo/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-svgo/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-svgo/manifest.json`:**
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

**Also in `build/pv-svgo/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-svgo --only static
python3 -I builder/gate.py pv-svgo --only nop
python3 -I builder/gate.py pv-svgo --only oracle
python3 -I builder/gate.py pv-svgo --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-svgo/`;
  - edit only `tasks/pv-svgo/`, `build/pv-svgo/` and, for pattern B, the register;
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
