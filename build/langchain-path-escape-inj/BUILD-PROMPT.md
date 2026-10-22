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

Project root: `/home/mara/cwe-bench`. Task: `langchain-path-escape-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-GR75-JV2W-4656 / CVE-2026-55443 - langchain-ai/langchain - path traversal / symlink-following escape from a configured root (CWE-22, CWE-59), plus non-segment-aware prefix allowlist. Whether a model-supplied path/glob pattern (and every file it expands to, after symlink resolution) stays inside the configured root_path / allowed vi
- Pinned (vulnerable) commit: 0392b6bae4bdfc0b7ed5aeb2e9e414bbb7ea643b. Published fix: dcaf7795a3e6590af55c3ff7bda6add6355e9ea6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "3596",
 "advisory_ids": [
  "GHSA-GR75-JV2W-4656",
  "CVE-2026-55443",
  "PYSEC-2026-2192",
  "PYSEC-2026-2556"
 ],
 "repo": "langchain-ai/langchain",
 "pinned_commit": "parent of dcaf7795a3e6590af55c3ff7bda6add6355e9ea6 (parent_commit not given in candidate)",
 "fix_commits": [
  "dcaf7795a3e6590af55c3ff7bda6add6355e9ea6"
 ],
 "trust_decision": {
  "summary": "Whether a model-supplied path/glob pattern (and every file it expands to, after symlink resolution) stays inside the configured root_path / allowed virtual prefix; decided in FilesystemFileSearchMiddleware (_validate_and_resolve_path validates only the base `path`, never the glob `pattern` or per-match resolved paths) and in langchain_anthropic's _validate_path / _FilesystemClaudeFileToolMiddleware._validate_and_resolve_path (raw str.startswith prefix test, not segment-aware).",
  "evidence": [
   "libs/langchain_v1/langchain/agents/middleware/file_search.py:236-258",
   "libs/langchain_v1/langchain/agents/middleware/file_search.py:160-168",
   "libs/langchain_v1/langchain/agents/middleware/file_search.py:328-342",
   "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:124-129",
   "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:848-857"
  ]
 },
 "landing_point": {
  "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:236-258",
  "why": "The summary says 'path traversal in file-search middleware'; the only visible traversal guard is _validate_and_resolve_path, which already rejects '..'/'~' and resolves the base path, so an engineer looks there first and may conclude the base path is fine without noticing the glob `pattern` and symlinked matches bypass it."
 },
 "fix_sites": [
  {
   "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:160-168",
   "entry_point": "FilesystemFileSearchMiddleware(...).glob_search tool (pattern arg rejected for leading '/' or '..' segments; per-match resolved containment)",
   "module_kind": "agent middleware tool (core langchain v1 package)"
  },
  {
   "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:296-301",
   "entry_point": "FilesystemFileSearchMiddleware(...).grep_search tool, ripgrep backend (_ripgrep_search result filtering)",
   "module_kind": "subprocess backend of the same tool"
  },
  {
   "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:328-352",
   "entry_point": "FilesystemFileSearchMiddleware(...).grep_search tool, Python fallback (_python_search; use_ripgrep=False or rg missing/timeout)",
   "module_kind": "second implementation (fallback) of grep in same file"
  },
  {
   "where": "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:124-129",
   "entry_point": "StateClaudeTextEditorMiddleware / StateClaudeMemoryMiddleware file tool (all commands via _validate_path, e.g. anthropic_tools.py:327, 537-540)",
   "module_kind": "partner package, state-backed virtual FS middleware"
  },
  {
   "where": "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:848-857",
   "entry_point": "FilesystemClaudeTextEditorMiddleware / FilesystemClaudeMemoryMiddleware file tool (view/create/str_replace/insert/delete/rename)",
   "module_kind": "partner package, real-filesystem middleware (separate distribution)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:124-129 and :848-857 (separate langchain-anthropic package re-implementing path validation for file tools); also the Python grep fallback libs/langchain_v1/langchain/agents/middleware/file_search.py:328-352"
 },
 "O3_reason_to_dismiss": "The report points at langchain_v1 file-search; the Anthropic text-editor/memory tools are a different partner package whose filesystem variant already resolves and root-contains the path (anthropic_tools.py:839-846), so the prefix check looks like a cosmetic namespacing feature rather than a security boundary; and the Python grep fallback 'only runs when ripgrep is unavailable'.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate in-root results must keep working: glob '*.py' / '**/...' patterns and file names containing '..' as a substring (fix only rejects whole '..' segments), in-root symlinks whose target is inside root, the exact prefix directory '/memories' itself and its descendants, and the 'No files found'/'No matches found' return contract instead of raising. An over-broad fix (reject any '..' substring in pattern, drop all symlinks, require trailing-slash prefix match) breaks these.",
  "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:160-175; libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:850-857"
 },
 "O6_input_shapes": [
  "glob pattern containing '..' segments (e.g. '../x')",
  "absolute glob pattern (leading '/')",
  "glob pattern beginning with '~' (not expanded by glob; covered by per-match containment)",
  "in-root symlinked file pointing outside root (glob, ripgrep, Python grep)",
  "in-root symlinked directory pointing outside root (Python grep walk, followlinks=False)",
  "sibling directory sharing textual prefix ('/memories2/...' vs '/memories') in state-backed _validate_path",
  "same sibling-prefix shape in filesystem-backed _validate_and_resolve_path",
  "exact prefix directory ('/memories') must remain accepted"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "StateFileSearchMiddleware grep_search scopes state files with raw file_path.startswith(base_path), so path '/memories' also searches '/memories2/...' (same non-segment-aware prefix mechanism; glob_search in the same class is segment-aware)",
   "where": "libs/partners/anthropic/langchain_anthropic/middleware/file_search.py:299-301",
   "reason_to_dismiss": "It only scopes a search over the agent's own state dict, has no allowed_prefixes or root, so it is a convenience filter, not a security boundary.",
   "distance": "same package as the anthropic_tools.py fix site, different file",
   "present_in_latest": "no",
   "latest_where": "latest/libs/partners/anthropic/langchain_anthropic/middleware/file_search.py:302-306"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:1033-1049",
   "sibling": "a 'copy' or 'list directory' command in the filesystem file tool that resolves only the parent or compares prefixes on the unresolved virtual path",
   "why_realistic": "Command handlers are added one by one alongside _handle_rename; a maintainer could easily build the destination from the unvalidated name."
  },
  {
   "where": "libs/langchain_v1/langchain/agents/middleware/file_search.py:177-230",
   "sibling": "a ripgrep option such as following symlinks ('--follow') or a 'files' listing mode that emits rg paths without per-result containment",
   "why_realistic": "Adding a follow-links or listing flag is a plausible feature request; ripgrep result filtering lives in a separate parse loop that is easy to skip."
  },
  {
   "where": "libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:134-156",
   "sibling": "_list_directory-style helper using a raw startswith without trailing slash for the state 'view directory' command",
   "why_realistic": "Same prefix idiom already appears in neighbouring helpers in this file and in file_search.py:300."
  }
 ],
 "O9_family": "path traversal / symlink-following escape from a configured root (CWE-22, CWE-59), plus non-segment-aware prefix allowlist",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.10)",
  "toolchain": "uv/pip editable installs of libs/langchain_v1, libs/core and libs/partners/anthropic; pytest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "libs/langchain_v1/tests/unit_tests/agents/middleware/implementations/test_file_search.py (has older TestPathTraversalSecurity); libs/partners/anthropic/tests/unit_tests/middleware/test_anthropic_tools.py (TestPathValidation). ripgrep optional; tests can use use_ripgrep=False."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "libs/langchain_v1/langchain/agents/middleware/file_search.py; libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a '..'/absolute check on the glob pattern in glob_search only, leaving symlinked matches, both grep backends and the Anthropic prefix boundary open."
 },
 "out_of_scope_notes": [
  "libs/core/langchain_core/prompts/loading.py:31-44 has a separate lexical-only path guard (allow_dangerous_paths) for prompt loaders; different advisory/protection, not pursued.",
  "libs/langchain/langchain_classic/storage/file_system.py:65-78 LocalFileStore has its own root containment; different protection, not pursued."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); assumed to be the parent of the fix commit as staged in repo/.",
  "Repo size in MB not measured (no shell); giant_repo/tiny_repo flags not assessed, but langchain monorepo is neither tiny nor >1.5 GB in typical checkouts.",
  "Whether the O8 StateFileSearchMiddleware grep prefix issue is considered within this advisory's protection is a judgement call; it has no configured security boundary.",
  "Advisory summary mentions 'loaders' but the fix diff touches no loader code; the advisory text itself was not available beyond the summary.",
  "Path.glob behaviour for absolute/'..' patterns differs across Python 3.10-3.13; not run."
 ]
}
  ```
- Published fix sites:   - libs/langchain_v1/langchain/agents/middleware/file_search.py:160-168 — entry point: FilesystemFileSearchMiddleware(...).glob_search tool (pattern arg rejected for leading '/' or '..' segments; per-match resolved containment) [agent middleware tool (core langchain v1 package)]
  - libs/langchain_v1/langchain/agents/middleware/file_search.py:296-301 — entry point: FilesystemFileSearchMiddleware(...).grep_search tool, ripgrep backend (_ripgrep_search result filtering) [subprocess backend of the same tool]
  - libs/langchain_v1/langchain/agents/middleware/file_search.py:328-352 — entry point: FilesystemFileSearchMiddleware(...).grep_search tool, Python fallback (_python_search; use_ripgrep=False or rg missing/timeout) [second implementation (fallback) of grep in same file]
  - libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:124-129 — entry point: StateClaudeTextEditorMiddleware / StateClaudeMemoryMiddleware file tool (all commands via _validate_path, e.g. anthropic_tools.py:327, 537-540) [partner package, state-backed virtual FS middleware]
  - libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:848-857 — entry point: FilesystemClaudeTextEditorMiddleware / FilesystemClaudeMemoryMiddleware file tool (view/create/str_replace/insert/delete/rename) [partner package, real-filesystem middleware (separate distribution)]
- Uncovered routes to confirm (pattern B):   - libs/partners/anthropic/langchain_anthropic/middleware/file_search.py:299-301 — StateFileSearchMiddleware grep_search scopes state files with raw file_path.startswith(base_path), so path '/memories' also searches '/memories2/...' (same non-segment-aware prefix mechanism; glob_search in the same class is segment-aware) (reason to dismiss: It only scopes a search over the agent's own state dict, has no allowed_prefixes or root, so it is a convenience filter, not a security boundary.; still in latest: no)
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring trust decision have beaten both models).

RECURRING DECISION / PROTECTED SINK: Whether a model-supplied path/glob pattern (and every file it expands to, after symlink resolution) stays inside the configured root_path / allowed virtual prefix; decided in FilesystemFileSearchMiddleware (_validate_and_resolve_path validates only the base `p

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: libs/partners/anthropic/langchain_anthropic/middleware/file_search.py:299-301 (StateFileSearchMiddleware grep_search scopes state file; dismiss: It only scopes a search over the agent's own ).
STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy at these recurring sites (verify each by reading the code): libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:1033-1049 -> a 'copy' or 'list directory' command in the filesystem file tool that  (realistic: Command handlers are added one by one alongside _handle_rena); libs/langchain_v1/langchain/agents/middleware/file_search.py:177-230 -> a ripgrep option such as following symlinks ('--follow') or a 'files'  (realistic: Adding a follow-links or listing flag is a plausible feature); libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py:134-156 -> _list_directory-style helper using a raw startswith without trailing s (realistic: Same prefix idiom already appears in neighbouring helpers in). Each sibling MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, placed where the published upstream fix never touches, and carry a DIFFERENT plausible reason-to-dismiss from the others (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-dismiss are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every injected sibling through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for exactly that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Legitimate in-root results must keep working: glob '*.py' / '**/...' patterns and file names containing '..' as a substring (fix only rejects whole '..' segments), in-root symlinks whose target is ins (near libs/langchain_v1/langchain/agents/middleware/file); keep every legitimate use of the mechanism working.

Aim for >=3 levers with DIFFERENT reasons to dismiss. Every sibling must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/sibling (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each sibling and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Python (>=3.10). Offline after build, no external services. INJECTED: siblings go in OUR copy only, register them. Recurring trust decision (4 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/langchain-path-escape-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/langchain-path-escape-inj/instruction.md`)
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

## Tests (`tasks/langchain-path-escape-inj/tests/`)
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
- **Wrong-fix patches** go in `build/langchain-path-escape-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/langchain-path-escape-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/langchain-path-escape-inj/manifest.json`:**
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

**Also in `build/langchain-path-escape-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py langchain-path-escape-inj --only static
python3 -I builder/gate.py langchain-path-escape-inj --only nop
python3 -I builder/gate.py langchain-path-escape-inj --only oracle
python3 -I builder/gate.py langchain-path-escape-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/langchain-path-escape-inj/`;
  - edit only `tasks/langchain-path-escape-inj/`, `build/langchain-path-escape-inj/` and, for pattern B, the register;
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
