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

Project root: `/home/mara/cwe-bench`. Task: `mjml-s3`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-4hch-r9xf-6vfr", "GHSA-45h5-66jx-r2wf"]; mjmlio/mjml; path traversal in file include resolution (CWE-36 absolute path traversal / CWE-22)
- Pinned (vulnerable) commit: 21034a7187f2bda4b0d66e7a1c63314c88dce71a. Published fix: 30e29ed2cdae, 517b376b068e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "s3-stk-mjml-ghsa45h5",
 "advisory_ids": [
  "GHSA-4hch-r9xf-6vfr",
  "GHSA-45h5-66jx-r2wf"
 ],
 "repo": "mjmlio/mjml",
 "pinned_commit": "21034a7187f2bda4b0d66e7a1c63314c88dce71a",
 "fix_commits": [
  "30e29ed2cdae",
  "517b376b068e"
 ],
 "trust_decision": {
  "summary": "Whether an mj-include path may name a file outside the project root is decided in the XML parser: handleInclude resolves decodeURIComponent(attrs.path) against cwd and calls fs.readFileSync with no containment check, and the only control is the caller-supplied ignoreIncludes flag, which defaults to false and which the public mjml2html entry point never forwards to the parser.",
  "evidence": [
   "packages/mjml-parser-xml/src/index.js:68-78",
   "packages/mjml-parser-xml/src/index.js:39",
   "packages/mjml-parser-xml/src/index.js:182-188",
   "packages/mjml-core/src/index.js:98-106"
  ]
 },
 "landing_point": {
  "where": "packages/mjml-parser-xml/src/index.js:68",
  "why": "The summary says mj-include directory traversal; handleInclude is the only code that turns the path attribute into a file read, resolving it with path.resolve(cwd, file) and reading it unconditionally."
 },
 "fix_sites": [
  {
   "where": "packages/mjml-parser-xml/src/index.js:39",
   "entry_point": "MJMLParser (mjml-parser-xml default export), reached from mjml2html",
   "module_kind": "parser / low-level library (sink owner)"
  },
  {
   "where": "packages/mjml-parser-xml/src/index.js:68-98",
   "entry_point": "MJMLParser (mjml-parser-xml default export), reached from mjml2html and directly from the CLI",
   "module_kind": "parser / low-level library (sink owner); fix adds isPathAllowed + denyInclude and a realpath containment check before readFileSync"
  },
  {
   "where": "fix.diff:155-165",
   "entry_point": "mj-include of a css/html partial (no counterpart at the pinned commit)",
   "module_kind": "parser helper handleCssHtmlInclude - edited by the published fix but absent from the pinned tree"
  },
  {
   "where": "packages/mjml-core/src/index.js:82-105",
   "entry_point": "mjml2html public API (exported by packages/mjml/src/index.js:49)",
   "module_kind": "core API options wrapper - must accept ignoreIncludes and forward it to MJMLParser"
  },
  {
   "where": "packages/mjml-cli/src/client.js:120-127",
   "entry_point": "mjml CLI (--config.* merged into the options passed to mjml2html at client.js:202)",
   "module_kind": "CLI config merge - must expose the opt-in (allowIncludes) and coerce the boolean"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "packages/mjml-cli/src/helpers/fileContext.js:28-63"
 },
 "O3_reason_to_dismiss": "The second include reader and the CLI validate route never emit rendered output - one only builds a chokidar watch list and the other only reports validator errors - so both can be argued to sit outside an advisory about compiled-HTML disclosure.",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Includes that stay inside the project must keep rendering when enabled: the parser's own 'Include' case resolves ./test/incl.mjml relative to filePath (packages/mjml-parser-xml/test/test-values.js:435-444) and the fix had to add ignoreIncludes:false to that test (packages/mjml-parser-xml/test/test.js:13-17); a realpath-rooted check also denies legitimate sibling includes written as ../partials/x from a subdirectory, because the nested MJMLParser call re-derives cwd from the included file's own dirname (packages/mjml-parser-xml/src/index.js:105-111), and denies symlinked partials.",
  "where": "packages/mjml-parser-xml/src/index.js:105-111"
 },
 "O6_input_shapes": [
  "relative include inside the project (./partials/x.mjml) - must still render when includes are enabled",
  "relative traversal (../outside.mjml)",
  "absolute path",
  "percent-encoded path, decodeURIComponent(attrs.path) before resolution (packages/mjml-parser-xml/src/index.js:186)",
  "symlink target resolved with fs.realpathSync (fix.diff:119-129)",
  "no option at all -> include silently ignored, and no denial comment emitted",
  "boolean option arriving as bare true and as the string 'true' from yargs --config (fix.diff:80-84)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "packages/mjml-core/src/index.js:71-105",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "mjml -v/--validate parses the input with MJMLParser({ components }) directly, so mj-include is followed with no containment check and the mjml2html option plumbing is bypassed entirely",
   "where": "packages/mjml-cli/src/client.js:196",
   "reason_to_dismiss": "Validate only produces validator errors, never rendered HTML, so an engineer can argue the include read there is not the reported disclosure and is out of scope",
   "distance": "mjml-cli package, two files from the landing point; reaches the parser sink one package below mjml-core",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/mjml-core/src/helpers/mjmlconfig.js:16-19",
   "sibling": ".mjmlconfig 'options' (merged over core defaults at packages/mjml-core/src/index.js:52-64 and 93-96) carrying ignoreIncludes, silently re-enabling includes",
   "why_realistic": "the file already exists to configure mjml2html options, so a maintainer adding an include policy there is a natural change and defeats a core-only default flip"
  },
  {
   "where": "packages/mjml-core/src/createComponent.js:71-81",
   "sibling": "renderMJML hardcodes ignoreIncludes:true; a later change that lets components opt back into includes would reopen the sink with no path check",
   "why_realistic": "custom components legitimately want partials, and this is already the one call site that special-cases the flag"
  },
  {
   "where": "packages/mjml-parser-xml/src/index.js:105-119",
   "sibling": "nested includes could forward a caller-supplied basePath/root instead of re-deriving cwd from the partial's dirname",
   "why_realistic": "it is the obvious fix for sibling-include behaviour and would move the containment root, changing which paths are allowed"
  },
  {
   "where": "packages/mjml-cli/src/commands/watchFiles.js:50-58",
   "sibling": "watch-mode compile rebuilds the mjml2html options from options.config per file, a second place an include policy must be honoured",
   "why_realistic": "it already re-merges config for every file, so adding an override there is a believable maintainer change"
  }
 ],
 "O9_family": "path traversal in file include resolution (CWE-36 absolute path traversal / CWE-22)",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (ES modules compiled by Babel 7)",
  "toolchain": "Node + Yarn workspaces + Lerna + Babel 7 with --root-mode upward; per-package 'build' emits lib/, tests run as plain node scripts (packages/mjml-parser-xml: node ./test/test.js)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/mjml-parser-xml/test/test.js (chai, run as node ./test/test.js) with the 'Include' case in test-values.js:435-444 against fixture test/incl.mjml; packages/mjml-core/tests/index.js covers helpers only; no include/CLI/validate tests exist at the pinned commit"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/mjml-core/src/index.js, packages/mjml-parser-xml/src/index.js, packages/mjml-cli/src/client.js",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a '..' / startsWith check inside handleInclude only (or just flip ignoreIncludes to true there), leaving mjml2html unable to forward the flag and the CLI -v route and watch-mode include reader untouched"
 },
 "out_of_scope_notes": [
  "packages/mjml-core/src/index.js:36-44 require()s an arbitrary path supplied through the public 'skeleton' option - a separate code-loading surface, not this advisory, not pursued.",
  "packages/mjml-core/src/helpers/mjmlconfig.js:16-19 reads .mjmlconfig JSON from a caller-supplied path - separate config surface, not pursued."
 ],
 "unverified": [
  "The published diff does not apply cleanly to the pinned tree: its mjml-core hunk targets 'export default async function mjml2html' around line 420 while the pinned file has the synchronous form at packages/mjml-core/src/index.js:32, and its parser hunk edits handleCssHtmlInclude, an identifier that does not exist anywhere at the pinned commit; the two fix commits each introduce ignoreIncludes in mjml-core from different bases. Treated as a behaviour spec, not a patch.",
  "Repo size in MB was not measured (no shell available); estimated well under 5 MB from the 223-file tracked tree and the absence of node_modules, so tiny_repo is asserted from the file inventory only.",
  "Whether the hidden tests require the exact denial contract (the literal '<!-- mj-include denied -->' comment and errors:[{type:'include-denied'}]) is unknown; nothing at the pinned commit produces or consumes it, and packages/mjml-validator/src/rules/errorAttr.js:10-17 only maps type 'include'.",
  "Whether defaulting ignoreIncludes to true is part of the intended task behaviour is unknown: it changes documented behaviour (packages/mjml/README.md:128 documents filePath-driven includes) and the published fix had to edit the parser's own Include test to opt in.",
  "present_in_latest for the O8 route is unknown because no latest release code was provided."
 ]
}
  ```
- Published fix sites:   - packages/mjml-parser-xml/src/index.js:39 — entry point: MJMLParser (mjml-parser-xml default export), reached from mjml2html [parser / low-level library (sink owner)]
  - packages/mjml-parser-xml/src/index.js:68-98 — entry point: MJMLParser (mjml-parser-xml default export), reached from mjml2html and directly from the CLI [parser / low-level library (sink owner); fix adds isPathAllowed + denyInclude and a realpath containment check before readFileSync]
  - fix.diff:155-165 — entry point: mj-include of a css/html partial (no counterpart at the pinned commit) [parser helper handleCssHtmlInclude - edited by the published fix but absent from the pinned tree]
  - packages/mjml-core/src/index.js:82-105 — entry point: mjml2html public API (exported by packages/mjml/src/index.js:49) [core API options wrapper - must accept ignoreIncludes and forward it to MJMLParser]
  - packages/mjml-cli/src/client.js:120-127 — entry point: mjml CLI (--config.* merged into the options passed to mjml2html at client.js:202) [CLI config merge - must expose the opt-in (allowIncludes) and coerce the boolean]
- Uncovered routes to confirm (pattern B):   - packages/mjml-cli/src/client.js:196 — mjml -v/--validate parses the input with MJMLParser({ components }) directly, so mj-include is followed with no containment check and the mjml2html option plumbing is bypassed entirely (reason to dismiss: Validate only produces validator errors, never rendered HTML, so an engineer can argue the include read there is not the reported disclosure and is out of scope; still in latest: unknown)
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

## Environment (`tasks/mjml-s3/environment/Dockerfile`)
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

## Report to the solver (`tasks/mjml-s3/instruction.md`)
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

## Tests (`tasks/mjml-s3/tests/`)
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
- **Wrong-fix patches** go in `build/mjml-s3/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/mjml-s3/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mjml-s3/manifest.json`:**
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

**Also in `build/mjml-s3/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py mjml-s3 --only static
python3 -I common/gate/gate.py mjml-s3 --only nop
python3 -I common/gate/gate.py mjml-s3 --only oracle
python3 -I common/gate/gate.py mjml-s3 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mjml-s3/`;
  - edit only `tasks/mjml-s3/`, `build/mjml-s3/` and, for pattern B, the register;
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
