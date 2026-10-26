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

Project root: `/home/mara/cwe-bench`. Task: `mcp-atlassian-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-2XJ6-XX86-CWWC", "CVE-2026-77255", "PYSEC-2026-4080"]; sooperset/mcp-atlassian; CWE-22 path traversal / arbitrary local file read with exfiltration through a confused-deputy upload (CWE-441)
- Pinned (vulnerable) commit: parent of b041733473f95119dd539542a43c280737a8e460 (parent_commit not given in candidate). Published fix: b041733473f95119dd539542a43c280737a8e460.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "278",
 "advisory_ids": [
  "GHSA-2XJ6-XX86-CWWC",
  "CVE-2026-77255",
  "PYSEC-2026-4080"
 ],
 "repo": "sooperset/mcp-atlassian",
 "pinned_commit": "parent of b041733473f95119dd539542a43c280737a8e460 (parent_commit not given in candidate)",
 "fix_commits": [
  "b041733473f95119dd539542a43c280737a8e460"
 ],
 "trust_decision": {
  "summary": "Whether a caller-supplied local file path (MCP tool argument) may be read by the server and sent to Atlassian; decided nowhere at the pinned commit on the upload side. The upload helpers only abspath + exists-check, and the workspace confinement helper validate_safe_path (CWD base) is applied only on the download side.",
  "evidence": [
   "src/mcp_atlassian/jira/attachments.py:372-389",
   "src/mcp_atlassian/confluence/attachments.py:151-169",
   "src/mcp_atlassian/servers/confluence.py:149-153",
   "src/mcp_atlassian/utils/io.py:23-58",
   "src/mcp_atlassian/jira/attachments.py:37-43"
  ]
 },
 "landing_point": {
  "where": "src/mcp_atlassian/servers/jira.py:1858-1867",
  "why": "The advisory title names Jira update_issue. Its `attachments` argument (file paths) is parsed at src/mcp_atlassian/servers/jira.py:1897-1922 and handed to JiraFetcher.update_issue."
 },
 "fix_sites": [
  {
   "where": "src/mcp_atlassian/jira/attachments.py:372-375",
   "entry_point": "MCP tool jira update_issue (attachments, or an `attachments` key inside the fields/additional_fields JSON) -> JiraFetcher.update_issue -> upload_attachments -> upload_attachment; also public Python API JiraFetcher.upload_attachment/upload_attachments",
   "module_kind": "lower_level_api (Jira client mixin, the actual sink)"
  },
  {
   "where": "src/mcp_atlassian/confluence/attachments.py:151-154",
   "entry_point": "MCP tools confluence upload_attachment (file_path) and upload_attachments (file_paths) -> ConfluenceFetcher.upload_attachment -> _upload_attachment_direct open() at src/mcp_atlassian/confluence/attachments.py:637-638",
   "module_kind": "second_implementation (Confluence product package)"
  },
  {
   "where": "src/mcp_atlassian/servers/confluence.py:149",
   "entry_point": "MCP tools confluence create_page and update_page (content_file) via _resolve_page_content at src/mcp_atlassian/servers/confluence.py:791 and :967",
   "module_kind": "wrapper_or_composition (tool-layer helper for a neighbouring feature: page body from file)"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/mcp_atlassian/confluence/attachments.py:151-154 (Confluence upload); also src/mcp_atlassian/servers/confluence.py:149 (content_file page-body read, a neighbouring feature, not an attachment)"
 },
 "O3_reason_to_dismiss": "The report is about Jira update_issue attachments. Confluence is a different product package, and content_file is a 'page body' feature that the docs explicitly describe as 'Absolute or relative filesystem path' (src/mcp_atlassian/servers/confluence.py:725-726, :1810), so a solver can call it intended behaviour and out of scope.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate uploads of files inside the workspace, by relative or absolute path, must keep working (the fix's tests patch os.getcwd and upload an absolute path under it). The base64 upload path must keep working, and so must the download side's existing confinement. A fix that rejects every absolute path or every file read breaks these.",
  "where": "src/mcp_atlassian/servers/confluence.py:1806-1819; src/mcp_atlassian/servers/confluence.py:1897-1913; fix.diff:1173-1184; fix.diff:1196-1218"
 },
 "O6_input_shapes": [
  "absolute path outside CWD (fix.diff:1547-1559)",
  "relative ../ traversal (fix.diff:1547-1559)",
  "list of paths via upload_attachments / update_issue (fix.diff:1566-1572)",
  "JSON-array string vs comma-separated string for update_issue attachments (src/mcp_atlassian/servers/jira.py:1899-1911)",
  "attachments key smuggled inside the fields/additional_fields JSON, merged into kwargs (src/mcp_atlassian/servers/jira.py:1918-1925)",
  "~ home expansion for content_file (src/mcp_atlassian/servers/confluence.py:149)",
  "symlink escape, via resolve() in validate_safe_path (src/mcp_atlassian/utils/io.py:46-51)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "src/mcp_atlassian/jira/issues.py:597",
   "sibling": "create_issue accepting an `attachments` list (as update_issue does) that uploads via a direct self.jira.add_attachment(filename=...) call instead of upload_attachment",
   "why_realistic": "update_issue already special-cases attachments at src/mcp_atlassian/jira/issues.py:1157 and 1229-1233, so attachments-on-create is an obvious feature request, and copying the add_attachment call skips the shared helper."
  },
  {
   "where": "src/mcp_atlassian/servers/jira.py:2120",
   "sibling": "a Jira add_comment `body_file` / update_issue `description_file` that reads a path with Path.read_text, mirroring Confluence content_file",
   "why_realistic": "content_file exists at src/mcp_atlassian/servers/confluence.py:117-153 for oversized bodies. A Jira equivalent is a natural parity feature and sits in another package from the Confluence helper."
  },
  {
   "where": "src/mcp_atlassian/servers/confluence.py:1237",
   "sibling": "a Confluence add_comment `content_file` that reuses an inline copy of the old read logic rather than _resolve_page_content",
   "why_realistic": "Comments take a body like pages do, and maintainers often duplicate small helpers per tool."
  }
 ],
 "O9_family": "CWE-22 path traversal / arbitrary local file read with exfiltration through a confused-deputy upload (CWE-441)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.10)",
  "toolchain": "hatchling / uv (pyproject.toml), pytest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/unit/jira/test_attachments.py, tests/unit/confluence/test_attachments.py, tests/unit/servers/test_confluence_server.py (Atlassian API mocked with MagicMock; fix.diff:1538-1564)"
 },
 "O11_fix_minutes": 30,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/mcp_atlassian/jira/attachments.py, src/mcp_atlassian/confluence/attachments.py, src/mcp_atlassian/servers/confluence.py (the published commit also touches 11 other source files for unrelated advisories: SSRF pinning, project/space filters, tool auth, OAuth file perms, callback XSS)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Validate only the `attachments` argument in the update_issue tool handler (src/mcp_atlassian/servers/jira.py:1897-1922). This misses the attachments key inside the fields/additional_fields JSON, the Confluence upload tools and content_file."
 },
 "out_of_scope_notes": [
  "The fix commit is an omnibus that bundles about 15 advisories (SSRF DNS pinning/redirects, JQL/CQL allowlist bypass, call-time tool authorization, global-credential fallback, OAuth token file perms, OAuth callback XSS, download into CWD root). A task copy would need to carve out only the upload/content_file hunks.",
  "src/mcp_atlassian/preprocessing/confluence.py:94-102: the md2conf converter runs with a temp root_dir. Not checked whether markdown image references can make it read local files."
 ],
 "unverified": [
  "repo_mb: not measured (no shell). About 108 Python files under src/, so tiny_repo (<5 MB source) may hold but is not flagged without a measurement.",
  "pinned_commit hash: the candidate gives parent_commit null; assumed to be the parent of the fix commit.",
  "Advisory text beyond the summary was not available; the 'list' confused-deputy path is inferred from the fix's test docstring (fix.diff:1520-1572).",
  "Whether md2conf (third-party) can read local files referenced from markdown was not checked.",
  "recall_risk: the fix test docstring lists about 15 GHSA ids for the same upload bug (fix.diff:1523-1524), which suggests wide write-up; the public coverage itself was not checked."
 ]
}
  ```
- Published fix sites:   - src/mcp_atlassian/jira/attachments.py:372-375 — entry point: MCP tool jira update_issue (attachments, or an `attachments` key inside the fields/additional_fields JSON) -> JiraFetcher.update_issue -> upload_attachments -> upload_attachment; also public Python API JiraFetcher.upload_attachment/upload_attachments [lower_level_api (Jira client mixin, the actual sink)]
  - src/mcp_atlassian/confluence/attachments.py:151-154 — entry point: MCP tools confluence upload_attachment (file_path) and upload_attachments (file_paths) -> ConfluenceFetcher.upload_attachment -> _upload_attachment_direct open() at src/mcp_atlassian/confluence/attachments.py:637-638 [second_implementation (Confluence product package)]
  - src/mcp_atlassian/servers/confluence.py:149 — entry point: MCP tools confluence create_page and update_page (content_file) via _resolve_page_content at src/mcp_atlassian/servers/confluence.py:791 and :967 [wrapper_or_composition (tool-layer helper for a neighbouring feature: page body from file)]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/mcp-atlassian-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/mcp-atlassian-mm/instruction.md`)
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

## Tests (`tasks/mcp-atlassian-mm/tests/`)
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
- **Wrong-fix patches** go in `build/mcp-atlassian-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/mcp-atlassian-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mcp-atlassian-mm/manifest.json`:**
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

**Also in `build/mcp-atlassian-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py mcp-atlassian-mm --only static
python3 -I builder/gate.py mcp-atlassian-mm --only nop
python3 -I builder/gate.py mcp-atlassian-mm --only oracle
python3 -I builder/gate.py mcp-atlassian-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mcp-atlassian-mm/`;
  - edit only `tasks/mcp-atlassian-mm/`, `build/mcp-atlassian-mm/` and, for pattern B, the register;
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
