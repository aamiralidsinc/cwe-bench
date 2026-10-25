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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-file-viewer`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-3753-M2X2-Q623", "CVE-2026-91127"]; flyfish-dev/file-viewer; XSS (CWE-79/CWE-83): unsafe URL schemes and attribute injection in generated HTML
- Pinned (vulnerable) commit: parent of ef045680f8d9830a3eee9612f7df46a734361b07 (parent_commit not given in candidate). Published fix: ef045680f8d9830a3eee9612f7df46a734361b07.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7789",
 "advisory_ids": [
  "GHSA-3753-M2X2-Q623",
  "CVE-2026-91127"
 ],
 "repo": "flyfish-dev/file-viewer",
 "pinned_commit": "parent of ef045680f8d9830a3eee9612f7df46a734361b07 (parent_commit not given in candidate)",
 "fix_commits": [
  "ef045680f8d9830a3eee9612f7df46a734361b07"
 ],
 "trust_decision": {
  "summary": "Which document-derived values (HYPERLINK field targets, font names, embedded attachment/image data URLs) may become href/style attribute content in the legacy DOC HTML renderer, and whether that HTML is put into the DOM unsanitized; decided in renderMsDoc's node renderers (packages/renderers/doc/src/render/html.ts) and at the two DOM mount points (doc viewer.ts mountMsDoc, renderer-word wordDoc.ts render).",
  "evidence": [
   "packages/renderers/doc/src/msdoc/parser.ts:64-73",
   "packages/renderers/doc/src/render/html.ts:193-203",
   "packages/renderers/doc/src/render/html.ts:41-46",
   "packages/renderers/doc/src/render/html.ts:170",
   "packages/renderers/doc/src/viewer.ts:30-34",
   "packages/renderers/word/src/wordDoc.ts:424-431"
  ]
 },
 "landing_point": {
  "where": "packages/renderers/doc/src/render/html.ts:199-201",
  "why": "Summary says 'unsafe hyperlink schemes in the legacy DOC renderer'; renderTextNode is the obvious place where node.href is emitted as <a href> with only HTML escaping."
 },
 "fix_sites": [
  {
   "where": "packages/renderers/doc/src/render/html.ts:199-201",
   "entry_point": "renderMsDoc / parseMsDocToHtml / createMsDocViewer / renderer-word .doc render (text hyperlink)",
   "module_kind": "core renderer (landing point)"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:255-257",
   "entry_point": "renderMsDoc (image fallback wrapped in hyperlink)",
   "module_kind": "core renderer, image node variant"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:262-264",
   "entry_point": "renderMsDoc (linked inline image)",
   "module_kind": "core renderer, image node variant"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:229-234",
   "entry_point": "renderMsDoc (image fallback asset href allowed any data:/blob:)",
   "module_kind": "core renderer, asset helper"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:268-275",
   "entry_point": "renderMsDoc (inline attachment dataUrl + hyperlink)",
   "module_kind": "core renderer, attachment node"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:377-380",
   "entry_point": "renderMsDoc (trailing embedded-attachments block)",
   "module_kind": "core renderer, neighbouring feature (attachments list)"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:170",
   "entry_point": "renderMsDoc (font-family from document font table)",
   "module_kind": "core renderer, CSS/style attribute (CWE-83)"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:41-46",
   "entry_point": "renderMsDoc (all style= attributes)",
   "module_kind": "shared serializer helper"
  },
  {
   "where": "packages/renderers/doc/src/render/html.ts:406-413",
   "entry_point": "renderMsDoc options (new externalLinkPolicy, default block)",
   "module_kind": "public API option / defaults"
  },
  {
   "where": "packages/renderers/doc/src/viewer.ts:30-34",
   "entry_point": "mountMsDoc / createMsDocViewer.load / createMsDocViewer.mount",
   "module_kind": "DOM mount helper (DOMPurify added)"
  },
  {
   "where": "packages/renderers/word/src/wordDoc.ts:424-431",
   "entry_point": "File Viewer standard component mounting a .doc via @file-viewer/renderer-word",
   "module_kind": "wrapper in another package (renderer-word); second DOM mount with its own innerHTML"
  }
 ],
 "O1_entry_points": 6,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "packages/renderers/word/src/wordDoc.ts:424-431 (separate package renderer-word does its own target.innerHTML of renderMsDoc output instead of calling mountMsDoc; fix also plumbs options.docx.externalLinkPolicy there, fix.diff:3192-3211)"
 },
 "O3_reason_to_dismiss": "renderer-word is the 'Word/DOCX' integration package, not the 'legacy DOC renderer' named in the advisory, and once renderMsDoc sanitizes hrefs its innerHTML looks safe; likewise the attachments list (html.ts:377-380) and font-family (html.ts:170) are 'not hyperlinks'.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Internal bookmark links (#name) must stay clickable even under the default block policy; with externalLinkPolicy 'allow', http(s)/mailto/tel and relative links must render; embedded attachments must stay downloadable as base64 data: URLs of non-active MIME types; data:image/* and https/blob inline images must still display.",
  "where": "packages/renderers/doc/src/render/html.ts:221-227; fix.diff:2912; fix.diff:2967-2979; fix.diff:573-586"
 },
 "O6_input_shapes": [
  "javascript: with mixed case and embedded newline/control chars (JaVa\\nScRiPt:)",
  "vbscript:, file:, blob: hyperlink targets",
  "data:text/html and other active data: MIME types (image/svg+xml, *+xml, text/javascript, application/xhtml+xml) as link or attachment href",
  "protocol-relative // and backslash-prefixed targets",
  "plain/./../ relative paths and #bookmark (must pass)",
  "href on text runs, linked images, image fallbacks, inline attachments, and the trailing attachments block",
  "font-family name containing quotes / attribute-breaking characters (style attribute injection)",
  "hyperlinks inside table cells (render context threaded through renderTableBlock)",
  "pre-parsed AST passed directly to renderMsDoc or the worker 'render' message (bypasses parser)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "packages/renderers/doc/src/msdoc/parser.ts:64-73 (HYPERLINK field instruction -> href) and parser.ts:279-282 (href attached to inline nodes)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "packages/renderers/word/src/wordDoc.ts:241",
   "sibling": "export/print toHtml path that re-serializes or re-renders the DOC HTML (e.g. from rendered.html rather than the mounted, purified DOM) into the print document without passing it through sanitizeMsDocHtml",
   "why_realistic": "Export adapter already builds HTML separately from the mount (prepareMsDocCloneForExport); a maintainer optimizing print could plausibly reuse rendered.html directly."
  },
  {
   "where": "packages/renderers/doc/src/msdoc/parser.ts:74-78",
   "sibling": "INCLUDEPICTURE / linked-object target surfaced as a clickable href (e.g. 'open linked file') without sanitizeMsDocLinkHref",
   "why_realistic": "The parser already extracts INCLUDEPICTURE targets; exposing them as a link for undisplayable images is a natural feature next to the image fallback at html.ts:249-258."
  },
  {
   "where": "packages/renderers/doc/src/viewer.ts:65-68",
   "sibling": "a second mount helper (e.g. mountMsDocPages / shadow-root mount) that writes rendered.html with innerHTML",
   "why_realistic": "renderer-word already duplicates mounting logic instead of calling mountMsDoc; another duplicate is in keeping with the codebase."
  }
 ],
 "O9_family": "XSS (CWE-79/CWE-83): unsafe URL schemes and attribute injection in generated HTML",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node + pnpm workspace (tsc / vite builds per package)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Per-package node verify scripts for the DOC renderer (packages/renderers/doc/scripts/verify-github-*.mjs, verify-table-spec.mjs use renderMsDoc on dist); browser sanitization harness apps/viewer-demo/scripts/verify-renderer-sanitization.mjs (Chromium via Playwright + Vite) gains DOC cases in the fix."
 },
 "O11_fix_minutes": 70,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/renderers/doc/src/render/html.ts, packages/renderers/doc/src/viewer.ts, packages/renderers/doc/src/types.ts, packages/renderers/doc/src/index.ts, packages/renderers/word/src/wordDoc.ts",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a javascript: blocklist to renderTextNode's href (or in parser.ts HYPERLINK decoding) and stop, leaving image/attachment hrefs, the attachments block, font-family style injection and the renderer-word innerHTML mount untouched."
 },
 "out_of_scope_notes": [
  "DOCX renderer has its own externalLinkPolicy handling (packages/renderers/word/src/wordDocx.ts:421-430); separate feature, not examined.",
  "WMF/EMF vector-to-SVG generation escapes attributes (packages/renderers/doc/src/msdoc/vector.ts:681-694); output is used as an image, not inspected further.",
  "Fix diff also changes SECURITY.md contact details; not source."
 ],
 "unverified": [
  "Repository size in MB not measured (no shell); monorepo with 57 npm targets and media assets, so tiny_repo is very unlikely but giant_repo not ruled out.",
  "pinned_commit hash not given (parent_commit null); assumed to be the immediate parent of the fix commit as provided in repo/.",
  "j_defence_ineffective=1 based on escapeHtml being applied to href (html.ts:200) and sanitizeAssetHref allowing any data:/blob: (html.ts:229-234), which did not stop scheme abuse; arguable whether these count as a 'defence present'.",
  "Whether the Playwright/Chromium harness runs fully offline after install not checked; a jsdom-based hidden test would avoid browser dependence.",
  "Recall risk judged low from publication date (2026-09) and project niche; external write-ups not checked."
 ]
}
  ```
- Published fix sites:   - packages/renderers/doc/src/render/html.ts:199-201 — entry point: renderMsDoc / parseMsDocToHtml / createMsDocViewer / renderer-word .doc render (text hyperlink) [core renderer (landing point)]
  - packages/renderers/doc/src/render/html.ts:255-257 — entry point: renderMsDoc (image fallback wrapped in hyperlink) [core renderer, image node variant]
  - packages/renderers/doc/src/render/html.ts:262-264 — entry point: renderMsDoc (linked inline image) [core renderer, image node variant]
  - packages/renderers/doc/src/render/html.ts:229-234 — entry point: renderMsDoc (image fallback asset href allowed any data:/blob:) [core renderer, asset helper]
  - packages/renderers/doc/src/render/html.ts:268-275 — entry point: renderMsDoc (inline attachment dataUrl + hyperlink) [core renderer, attachment node]
  - packages/renderers/doc/src/render/html.ts:377-380 — entry point: renderMsDoc (trailing embedded-attachments block) [core renderer, neighbouring feature (attachments list)]
  - packages/renderers/doc/src/render/html.ts:170 — entry point: renderMsDoc (font-family from document font table) [core renderer, CSS/style attribute (CWE-83)]
  - packages/renderers/doc/src/render/html.ts:41-46 — entry point: renderMsDoc (all style= attributes) [shared serializer helper]
  - packages/renderers/doc/src/render/html.ts:406-413 — entry point: renderMsDoc options (new externalLinkPolicy, default block) [public API option / defaults]
  - packages/renderers/doc/src/viewer.ts:30-34 — entry point: mountMsDoc / createMsDocViewer.load / createMsDocViewer.mount [DOM mount helper (DOMPurify added)]
  - packages/renderers/word/src/wordDoc.ts:424-431 — entry point: File Viewer standard component mounting a .doc via @file-viewer/renderer-word [wrapper in another package (renderer-word); second DOM mount with its own innerHTML]
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

## Environment (`tasks/pv-file-viewer/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-file-viewer/instruction.md`)
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

## Tests (`tasks/pv-file-viewer/tests/`)
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
- **Wrong-fix patches** go in `build/pv-file-viewer/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-file-viewer/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-file-viewer/manifest.json`:**
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

**Also in `build/pv-file-viewer/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-file-viewer --only static
python3 -I builder/gate.py pv-file-viewer --only nop
python3 -I builder/gate.py pv-file-viewer --only oracle
python3 -I builder/gate.py pv-file-viewer --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-file-viewer/`;
  - edit only `tasks/pv-file-viewer/`, `build/pv-file-viewer/` and, for pattern B, the register;
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
