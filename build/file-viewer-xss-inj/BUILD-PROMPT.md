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

Project root: `/home/mara/cwe-bench`. Task: `file-viewer-xss-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-3753-M2X2-Q623 / CVE-2026-91127 - flyfish-dev/file-viewer - XSS (CWE-79/CWE-83): unsafe URL schemes and attribute injection in generated HTML. Which document-derived values (HYPERLINK field targets, font names, embedded attachment/image data URLs) may become href/style attribute content in th
- Pinned (vulnerable) commit: 772ae40de07e48134de0449997cb4924b0cde3e4. Published fix: ef045680f8d9830a3eee9612f7df46a734361b07.
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
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring check have beaten both models; the mined batch was all solved).

RECURRING CHECK / PROTECTED SINK: Which document-derived values (HYPERLINK field targets, font names, embedded attachment/image data URLs) may become href/style attribute content in the legacy DOC HTML renderer, and whether that HTML is put into the DOM unsanitized; decided in renderMsDoc's no

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: none noted.
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): packages/renderers/word/src/wordDoc.ts:241 -> export/print toHtml path that re-serializes or re-renders the DOC HTML (realistic: Export adapter already builds HTML separately from the mount); packages/renderers/doc/src/msdoc/parser.ts:74-78 -> INCLUDEPICTURE / linked-object target surfaced as a clickable href (e. (realistic: The parser already extracts INCLUDEPICTURE targets; exposing); packages/renderers/doc/src/viewer.ts:65-68 -> a second mount helper (e.g. mountMsDocPages / shadow-root mount) that  (realistic: renderer-word already duplicates mounting logic instead of c). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Internal bookmark links (#name) must stay clickable even under the default block policy; with externalLinkPolicy 'allow', http(s)/mailto/tel and relative links must render; embedded attachments must s (near packages/renderers/doc/src/render/html.ts:221-227;); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: TypeScript. Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (6 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/file-viewer-xss-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/file-viewer-xss-inj/instruction.md`)
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

## Tests (`tasks/file-viewer-xss-inj/tests/`)
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
- **Wrong-fix patches** go in `build/file-viewer-xss-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/file-viewer-xss-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/file-viewer-xss-inj/manifest.json`:**
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

**Also in `build/file-viewer-xss-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py file-viewer-xss-inj --only static
python3 -I builder/gate.py file-viewer-xss-inj --only nop
python3 -I builder/gate.py file-viewer-xss-inj --only oracle
python3 -I builder/gate.py file-viewer-xss-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/file-viewer-xss-inj/`;
  - edit only `tasks/file-viewer-xss-inj/`, `build/file-viewer-xss-inj/` and, for pattern B, the register;
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
