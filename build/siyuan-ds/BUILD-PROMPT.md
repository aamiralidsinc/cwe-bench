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

Project root: `/home/mara/cwe-bench`. Task: `siyuan-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-FGMR-7W36-9QFQ", "CVE-2026-72796", "GO-2026-6423"]; siyuan-note/siyuan; CWE-862 missing authorization on alternate (static-file) channel; publish/reader access control bypass
- Pinned (vulnerable) commit: parent of 34be6c0bb0739d5b8e99ecc0cbfb474abb16230d (parent_commit not given in candidate). Published fix: 34be6c0bb0739d5b8e99ecc0cbfb474abb16230d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "17389",
 "advisory_ids": [
  "GHSA-FGMR-7W36-9QFQ",
  "CVE-2026-72796",
  "GO-2026-6423"
 ],
 "repo": "siyuan-note/siyuan",
 "pinned_commit": "parent of 34be6c0bb0739d5b8e99ecc0cbfb474abb16230d (parent_commit not given in candidate)",
 "fix_commits": [
  "34be6c0bb0739d5b8e99ecc0cbfb474abb16230d"
 ],
 "trust_decision": {
  "summary": "Whether a publish-service reader (RoleReader/RoleVisitor, injected for every proxied request) may read a static resource: the REST API applies publish rules (DisabledInPublish filters, templates denied, per-document publish access), but the kernel's static-file route handlers in kernel/server/serve.go only call CheckAuth, which admits readers.",
  "evidence": [
   "kernel/server/proxy/publish.go:229-230",
   "kernel/model/session.go:207-216",
   "kernel/model/role.go:40-45",
   "kernel/api/snippet.go:63-68",
   "kernel/api/petal.go:42-44",
   "kernel/api/file.go:551-558",
   "kernel/api/file.go:498-506",
   "kernel/server/serve.go:413-431",
   "kernel/server/serve.go:439-479",
   "kernel/server/serve.go:325"
  ]
 },
 "landing_point": {
  "where": "kernel/server/serve.go:428-431",
  "why": "The summary names templates first, and serveTemplates sits beside serveSnippets and serveExport in the one file that registers static routes. The neighbouring /assets/ handler already shows the reader publish-access pattern at kernel/server/serve.go:760-766."
 },
 "fix_sites": [
  {
   "where": "kernel/server/serve.go:325",
   "entry_point": "GET /export/*filepath (export artifacts, incl. /export/temp/)",
   "module_kind": "HTTP static/download handler"
  },
  {
   "where": "kernel/server/serve.go:414-415",
   "entry_point": "GET|HEAD /widgets/*filepath",
   "module_kind": "HTTP static route (gin Static)"
  },
  {
   "where": "kernel/server/serve.go:419-420",
   "entry_point": "GET|HEAD /plugins/*filepath",
   "module_kind": "HTTP static route (gin Static)"
  },
  {
   "where": "kernel/server/serve.go:424-425",
   "entry_point": "GET|HEAD /emojis/*filepath",
   "module_kind": "HTTP static route (gin Static)"
  },
  {
   "where": "kernel/server/serve.go:429-430",
   "entry_point": "GET|HEAD /templates/*filepath",
   "module_kind": "HTTP static route (gin Static)"
  },
  {
   "where": "kernel/server/serve.go:440-479",
   "entry_point": "GET /snippets/*filepath (conf.json snippet match + filesystem fallback)",
   "module_kind": "HTTP hand-written static handler"
  },
  {
   "where": "fix.diff:43-208",
   "entry_point": "new model helpers called from the /widgets/, /plugins/, /emojis/, /snippets/ handlers (kernel/model/publish_resource_access.go)",
   "module_kind": "model-layer access check + document-reference mapper"
  }
 ],
 "O1_entry_points": 6,
 "O2_out_of_scope_site": {
  "kind": "legacy_path",
  "where": "kernel/server/serve.go:465-479 (snippets filesystem fallback 'look on the filesystem when not found in conf.json'); fixed so readers get 404 there (fix.diff:472-482, test fix.diff:784-786)"
 },
 "O3_reason_to_dismiss": "Files in data/snippets that are not in conf.json have no DisabledInPublish flag, so a solver can argue the publish toggle doesn't apply and leave the fallback open to readers. Likewise /plugins/ and /emojis/ aren't named in the summary, and the REST API applies no per-document emoji/widget rule a solver could mirror.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Published pages must keep loading publish-enabled snippets, enabled plugins, and the widgets and custom emojis referenced by documents the reader can access. Admins (including the localhost admin shortcut for /export/) must keep templates and export downloads, a symlinked top-level plugin/widget package directory must still serve, and /public/ stays anonymous. A blanket CheckAdminRole on /widgets/ /plugins/ /emojis/ /snippets/ would break published pages.",
  "where": "kernel/model/session.go:298-303; kernel/server/serve.go:433-436; fix.diff:414-443; fix.diff:565-573; fix.diff:777-780"
 },
 "O6_input_shapes": [
  "path traversal in the wildcard ('..', '/package/../../secret') rejected by cleanStaticRelativePath (fix.diff:522-530)",
  "directory request served as <dir>/index.html (fix.diff:554-556)",
  "symlinked top-level package dir allowed; nested symlink escaping the package rejected (fix.diff:563-577)",
  "HEAD as well as GET (fix.diff:516-517)",
  "snippet matched by name + extension type, found/not-found/disabled distinguished (fix.diff:472-482)",
  "snippet on disk but absent from conf.json (filesystem fallback) hidden from readers (fix.diff:784-786)",
  "widget/emoji references as relative paths, localhost absolute URLs, HTML-escaped attribute values, external hosts ignored (fix.diff:186-200, 250-254)",
  "widget referenced from widget, iframe, HTML block or inline HTML nodes, any attribute (fix.diff:151-152, 177-183)",
  "nested custom-emoji subdirectory paths (fix.diff:93-99, 202-207)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "fix.diff:119-146 (getPublishResourceRefs builds, per accessible document, the set of referenced widget packages and emoji paths, cached by doc Updated). Nothing like it exists at the pinned commit; the REST-side equivalent for assets is kernel/model/publish_access.go:337-369",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "POST /api/bazaar/getInstalledTemplate lists installed template packages to readers (CheckAuth only), while the fix makes /templates/ admin-only",
   "where": "kernel/api/router.go:464",
   "reason_to_dismiss": "Returns package metadata, not template file contents, and it's a bazaar/marketplace API rather than a static-file route",
   "distance": "different package (kernel/api, router.go + bazaar.go) from the serve.go fix",
   "present_in_latest": "no",
   "latest_where": "latest/kernel/apicontract/contracts.go:809"
  },
  {
   "route": "POST /api/bazaar/getInstalledWidget and /api/bazaar/getInstalledPlugin list all installed widgets/plugins (including disabledInPublish ones) to readers",
   "where": "kernel/api/router.go:452",
   "reason_to_dismiss": "Metadata listing in the marketplace feature; the advisory is about static files",
   "distance": "kernel/api/router.go:452,456 and kernel/api/bazaar.go:126-146,236-253; other package from the fix",
   "present_in_latest": "no",
   "latest_where": "latest/kernel/apicontract/contracts.go:791"
  },
  {
   "route": "POST /api/system/getEmojiConf enumerates every custom emoji name under data/emojis to readers, regardless of whether an accessible document references it",
   "where": "kernel/api/router.go:47",
   "reason_to_dismiss": "Readers need the emoji picker conf to render; names only, no file bytes",
   "distance": "kernel/api/system.go:163-232; other package from the fix",
   "present_in_latest": "yes",
   "latest_where": "latest/kernel/apicontract/contracts.go:1355"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "kernel/server/serve.go:538-599",
   "sibling": "a reader-gated subpath under /appearance/ (e.g. a user-supplied data directory served through the same hand-written handler) that skips the publish check",
   "why_realistic": "CheckAuth already special-cases /appearance/ (kernel/model/session.go:290-295) and the handler is hand-rolled like /snippets/, so a maintainer could add a data-backed subpath there"
  },
  {
   "where": "kernel/server/serve.go:788-795",
   "sibling": "a reader-reachable sibling of /history/ or /repo/diff/ that serves stored copies of snippets/templates without CheckAdminRole",
   "why_realistic": "history snapshots contain data/templates and data/snippets copies, and the existing routes differ only by middleware list"
  }
 ],
 "O9_family": "CWE-862 missing authorization on alternate (static-file) channel; publish/reader access control bypass",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (kernel); TypeScript frontend not needed for these handlers",
  "toolchain": "go 1.26 (kernel/go.mod:3), cgo for go-sqlite3 fork (kernel/go.mod:53, kernel/go.mod:224)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "kernel/server/serve_assets_test.go and kernel/server/serve_svg_test.go (httptest + gin with RoleContextKey injection), kernel/model/publish_access_test.go; the fix adds kernel/server/serve_static_test.go and kernel/model/publish_resource_access_test.go using the same style"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "kernel/server/serve.go, kernel/model/publish_resource_access.go (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add model.CheckAdminRole to /templates/, /export/ and /snippets/ (or filter DisabledInPublish only on conf.json matches), leaving /widgets/, /plugins/, /emojis/ and the snippet filesystem fallback open to readers"
 },
 "out_of_scope_notes": [
  "/appearance/ is exempted from auth entirely when an access code is set (kernel/model/session.go:290-295); serves themes, not publish-controlled content.",
  "/export/ path decoding with url.PathUnescape after TrimPrefix (kernel/server/serve.go:353-360) is a path-handling quirk unrelated to the reader check."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); assumed the repo directory is the fix commit's parent.",
  "Repo size in MB not measured.",
  "Fairness risk: the per-document widget/emoji rule (only resources referenced by reader-accessible docs) is a design choice that a solver may not infer from a short report; hidden tests for /emojis/ and /widgets/ would need the report to state it.",
  "Did not check whether publish-mode frontend actually requests /templates/ or /export/ for readers (affects how O5 tests should be phrased).",
  "Whether O8 metadata-listing routes count as the 'same protected sink' is debatable; they expose names/metadata, not file bytes."
 ]
}
  ```
- Published fix sites:   - kernel/server/serve.go:325 — entry point: GET /export/*filepath (export artifacts, incl. /export/temp/) [HTTP static/download handler]
  - kernel/server/serve.go:414-415 — entry point: GET|HEAD /widgets/*filepath [HTTP static route (gin Static)]
  - kernel/server/serve.go:419-420 — entry point: GET|HEAD /plugins/*filepath [HTTP static route (gin Static)]
  - kernel/server/serve.go:424-425 — entry point: GET|HEAD /emojis/*filepath [HTTP static route (gin Static)]
  - kernel/server/serve.go:429-430 — entry point: GET|HEAD /templates/*filepath [HTTP static route (gin Static)]
  - kernel/server/serve.go:440-479 — entry point: GET /snippets/*filepath (conf.json snippet match + filesystem fallback) [HTTP hand-written static handler]
  - fix.diff:43-208 — entry point: new model helpers called from the /widgets/, /plugins/, /emojis/, /snippets/ handlers (kernel/model/publish_resource_access.go) [model-layer access check + document-reference mapper]
- Uncovered routes to confirm (pattern B):   - kernel/api/router.go:464 — POST /api/bazaar/getInstalledTemplate lists installed template packages to readers (CheckAuth only), while the fix makes /templates/ admin-only (reason to dismiss: Returns package metadata, not template file contents, and it's a bazaar/marketplace API rather than a static-file route; still in latest: no)
  - kernel/api/router.go:452 — POST /api/bazaar/getInstalledWidget and /api/bazaar/getInstalledPlugin list all installed widgets/plugins (including disabledInPublish ones) to readers (reason to dismiss: Metadata listing in the marketplace feature; the advisory is about static files; still in latest: no)
  - kernel/api/router.go:47 — POST /api/system/getEmojiConf enumerates every custom emoji name under data/emojis to readers, regardless of whether an accessible document references it (reason to dismiss: Readers need the emoji picker conf to render; names only, no file bytes; still in latest: yes)
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

## Environment (`tasks/siyuan-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/siyuan-ds/instruction.md`)
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

## Tests (`tasks/siyuan-ds/tests/`)
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
- **Wrong-fix patches** go in `build/siyuan-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/siyuan-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/siyuan-ds/manifest.json`:**
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

**Also in `build/siyuan-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py siyuan-ds --only static
python3 -I builder/gate.py siyuan-ds --only nop
python3 -I builder/gate.py siyuan-ds --only oracle
python3 -I builder/gate.py siyuan-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/siyuan-ds/`;
  - edit only `tasks/siyuan-ds/`, `build/siyuan-ds/` and, for pattern B, the register;
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
