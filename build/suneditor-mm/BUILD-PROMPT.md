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

Project root: `/home/mara/cwe-bench`. Task: `suneditor-mm`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-W93Q-CQ9W-58P7", "CVE-2026-54606"]; jihong88/suneditor; CWE-79 DOM XSS: unvalidated script/iframe content from pasted embed HTML executed in the editor page
- Pinned (vulnerable) commit: parent of 9d43a5e082101d2d6475cba86e0d58d7c2cf6677 (parent_commit not given in candidate). Published fix: 9d43a5e082101d2d6475cba86e0d58d7c2cf6677.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "14417",
 "advisory_ids": [
  "GHSA-W93Q-CQ9W-58P7",
  "CVE-2026-54606"
 ],
 "repo": "jihong88/suneditor",
 "pinned_commit": "parent of 9d43a5e082101d2d6475cba86e0d58d7c2cf6677 (parent_commit not given in candidate)",
 "fix_commits": [
  "9d43a5e082101d2d6475cba86e0d58d7c2cf6677"
 ],
 "trust_decision": {
  "summary": "Embed plugin decides which parts of user-pasted raw embed HTML (<iframe>/<blockquote> code) may run in the editor page: at the pinned commit any top-level <script src> is re-created as a live script and iframe srcs are not checked; the fix adds a script-src whitelist (default empty) in #create and an iframe URL-pattern check in submitSRC.",
  "evidence": [
   "src/plugins/modal/embed.js:446-449",
   "src/plugins/modal/embed.js:606-612",
   "src/plugins/modal/embed.js:644-652",
   "fix.diff:55-65",
   "fix.diff:74-80"
  ]
 },
 "landing_point": {
  "where": "src/plugins/modal/embed.js:609",
  "why": "The summary says 'external script element after iframe embed' in the Embed plugin; the only place a script element is created in the embed plugin is the createElement('script') call in #create."
 },
 "fix_sites": [
  {
   "where": "src/plugins/modal/embed.js:606-610",
   "entry_point": "Embed modal submit (modalAction -> submitSRC -> onEmbedInputBefore handler -> #create); also reached by the public plugin method submitSRC(src) and by an onEmbedInputBefore callback returning a replacement info object",
   "module_kind": "plugin, component creation (private #create)"
  },
  {
   "where": "src/plugins/modal/embed.js:446-449",
   "entry_point": "Embed modal submit / public submitSRC(src) with raw HTML starting with <iframe or <blockquote",
   "module_kind": "plugin, input parsing (public submitSRC)"
  },
  {
   "where": "src/plugins/modal/embed.js:158-172",
   "entry_point": "Plugin construction with pluginOptions (new scriptSrcWhitelist option, default [])",
   "module_kind": "plugin options defaults"
  },
  {
   "where": "src/plugins/modal/embed.js:119-126",
   "entry_point": "New static helper #isAllowedScriptSrc added next to #checkContentType (fix.diff:34-37), called only from #create",
   "module_kind": "plugin, validation helper"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "All source changes are in src/plugins/modal/embed.js (plus mirrored types in types/plugins/modal/embed.d.ts); no second implementation, wrapper or other module was touched."
 },
 "O3_reason_to_dismiss": "The advisory names the external <script> element; a solver can argue that other markup in the pasted embed code (srcdoc on an allowed iframe, inline event-handler attributes on sibling elements, children replaced by an integrator's onEmbedInputBefore callback) is 'the user's own embed markup' or 'trusted integrator data', not the script-element issue.",
 "O4_distance": {
  "files": 0,
  "packages": 0,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Provider blockquote embeds (Twitter/Instagram) that need their widgets.js must keep loading when that src is whitelisted, and URL-based embeds (process branch) and whitelisted iframe embed code must keep inserting; a fix that drops all scripts or rejects all raw HTML breaks these.",
  "where": "src/plugins/modal/embed.js:644-652; src/plugins/modal/embed.js:594-599; fix.diff:9-19"
 },
 "O6_input_shapes": [
  "raw HTML starting with <iframe (top-level iframe src checked, fix.diff:58)",
  "raw HTML starting with <blockquote containing nested iframes (fix.diff:59-63)",
  "top-level <script src=...> sibling after the embed element (fix.diff:76-80)",
  "inline <script> with no src (always rejected, fix.diff:35)",
  "whitelist entries as RegExp vs string prefix (fix.diff:36)"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "src/plugins/modal/embed.js:446-449 (DOMParser produces the children list consumed by #create at src/plugins/modal/embed.js:601-612)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "Allowed-looking iframe in raw embed HTML carrying a srcdoc attribute: the fix checks only getAttribute('src'), and the iframe is inserted as-is (no #setIframeAttrs on the raw path), so same-origin srcdoc content runs in the editor page.",
   "where": "src/plugins/modal/embed.js:601-612",
   "reason_to_dismiss": "The iframe's src is on the provider whitelist; srcdoc looks like an iframe attribute question, not the script-element issue the advisory names.",
   "distance": "same file, same function as the fix sites",
   "present_in_latest": "yes",
   "latest_where": "latest/src/plugins/modal/embed.js:509"
  },
  {
   "route": "Non-script top-level siblings in raw embed HTML (e.g. elements with inline event-handler attributes) are appended unfiltered to the cover and inserted into the live editor DOM.",
   "where": "src/plugins/modal/embed.js:612",
   "reason_to_dismiss": "The advisory is about <script> elements; arbitrary attributes on pasted embed markup look like general HTML sanitization, a neighbouring feature.",
   "distance": "same file, same loop as the script check",
   "present_in_latest": "yes",
   "latest_where": "latest/src/plugins/modal/embed.js:703"
  },
  {
   "route": "onEmbedInputBefore callback returning an info object with replaced children: handler(result) reaches #create without the new submitSRC iframe check (the script whitelist in #create still applies).",
   "where": "src/plugins/modal/embed.js:462-474",
   "reason_to_dismiss": "The data comes from the integrator's own event callback, so it can be argued to be trusted.",
   "distance": "same file",
   "present_in_latest": "yes",
   "latest_where": "latest/src/plugins/modal/embed.js:553"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/plugins/modal/video/index.js:663-667",
   "sibling": "Video plugin's raw <iframe> embed-code path could keep provider <script src> siblings the same way the embed plugin does.",
   "why_realistic": "It already parses pasted iframe embed code with DOMParser; supporting provider loader scripts there mirrors embed.js and would plausibly be added without the whitelist."
  },
  {
   "where": "src/plugins/modal/embed.js:572-589",
   "sibling": "The update (isUpdate) branch of #create could accept raw embed HTML and re-create its scripts when replacing an existing embed.",
   "why_realistic": "The update branch currently only swaps src; extending 'edit embed' to accept pasted code is a natural feature that would duplicate the create-branch loop."
  }
 ],
 "O9_family": "CWE-79 DOM XSS: unvalidated script/iframe content from pasted embed HTML executed in the editor page",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (ES modules)",
  "toolchain": "Node.js + npm; jest 30 with jest-environment-jsdom (package.json:66, package.json:117-118); playwright for e2e",
  "services": [],
  "offline_after_build": true,
  "project_tests": "test/unit/plugins/modal/embed.spec.js (jest/jsdom unit tests for submitSRC and #create; the fix changes the test at test/unit/plugins/modal/embed.spec.js:520)"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/plugins/modal/embed.js (types/plugins/modal/embed.d.ts for types only)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Drop or whitelist the <script> child in #create only, leaving iframe src/srcdoc and other pasted markup unchecked."
 },
 "out_of_scope_notes": [
  "src/core/logic/panel/viewer.js:786-795 removes head <script> in full-page code view only when 'script' is NOT disallowed, which looks inverted; general editor filter, not this advisory's protection; not pursued.",
  "Embed URL patterns used by #checkContentType (src/plugins/modal/embed.js:206, 220, 228) are unanchored, so the fix's new iframe-src check may accept non-provider schemes containing a provider host substring; not pursued."
 ],
 "unverified": [
  "repo_mb: size could not be measured without a shell; tiny_repo/giant_repo not assessed.",
  "pinned_commit hash: candidate parent_commit is null; recorded as parent of the fix commit.",
  "Whether a later editor pass (history/getContents/html.clean) strips srcdoc or on* attributes after component.insert (src/core/logic/shell/component.js:126-162 shows no sanitization at insert time); execution at insert time was not run.",
  "O1 counts the modal UI and the public submitSRC API; the onEmbedInputBefore object override is a third, integrator-controlled route into #create.",
  "O13 recall risk is judged from the advisory date (2026-08-26) and project size; no write-ups were searched."
 ]
}
  ```
- Published fix sites:   - src/plugins/modal/embed.js:606-610 — entry point: Embed modal submit (modalAction -> submitSRC -> onEmbedInputBefore handler -> #create); also reached by the public plugin method submitSRC(src) and by an onEmbedInputBefore callback returning a replacement info object [plugin, component creation (private #create)]
  - src/plugins/modal/embed.js:446-449 — entry point: Embed modal submit / public submitSRC(src) with raw HTML starting with <iframe or <blockquote [plugin, input parsing (public submitSRC)]
  - src/plugins/modal/embed.js:158-172 — entry point: Plugin construction with pluginOptions (new scriptSrcWhitelist option, default []) [plugin options defaults]
  - src/plugins/modal/embed.js:119-126 — entry point: New static helper #isAllowedScriptSrc added next to #checkContentType (fix.diff:34-37), called only from #create [plugin, validation helper]
- Uncovered routes to confirm (pattern B):   - src/plugins/modal/embed.js:601-612 — Allowed-looking iframe in raw embed HTML carrying a srcdoc attribute: the fix checks only getAttribute('src'), and the iframe is inserted as-is (no #setIframeAttrs on the raw path), so same-origin srcdoc content runs in the editor page. (reason to dismiss: The iframe's src is on the provider whitelist; srcdoc looks like an iframe attribute question, not the script-element issue the advisory names.; still in latest: yes)
  - src/plugins/modal/embed.js:612 — Non-script top-level siblings in raw embed HTML (e.g. elements with inline event-handler attributes) are appended unfiltered to the cover and inserted into the live editor DOM. (reason to dismiss: The advisory is about <script> elements; arbitrary attributes on pasted embed markup look like general HTML sanitization, a neighbouring feature.; still in latest: yes)
  - src/plugins/modal/embed.js:462-474 — onEmbedInputBefore callback returning an info object with replaced children: handler(result) reaches #create without the new submitSRC iframe check (the script whitelist in #create still applies). (reason to dismiss: The data comes from the integrator's own event callback, so it can be argued to be trusted.; still in latest: yes)
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

## Environment (`tasks/suneditor-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/suneditor-mm/instruction.md`)
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

## Tests (`tasks/suneditor-mm/tests/`)
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
- **Wrong-fix patches** go in `build/suneditor-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/suneditor-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/suneditor-mm/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/suneditor-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py suneditor-mm --only static
python3 -I builder/gate.py suneditor-mm --only nop
python3 -I builder/gate.py suneditor-mm --only oracle
python3 -I builder/gate.py suneditor-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/suneditor-mm/`;
  - edit only `tasks/suneditor-mm/`, `build/suneditor-mm/` and, for pattern B, the register;
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
