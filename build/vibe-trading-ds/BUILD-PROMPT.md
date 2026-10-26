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

Project root: `/home/mara/cwe-bench`. Task: `vibe-trading-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-5RMQ-CHC7-M22F"]; hkuds/vibe-trading; path traversal / unrestricted file read (CWE-22/23, CWE-552) via agent tools
- Pinned (vulnerable) commit: unknown (parent of 9454d4a27a763b80e1d6eb5763b86c88e9e4e714; parent_commit not supplied). Published fix: 9454d4a27a763b80e1d6eb5763b86c88e9e4e714.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "1246",
 "advisory_ids": [
  "GHSA-5RMQ-CHC7-M22F"
 ],
 "repo": "hkuds/vibe-trading",
 "pinned_commit": "unknown (parent of 9454d4a27a763b80e1d6eb5763b86c88e9e4e714; parent_commit not supplied)",
 "fix_commits": [
  "9454d4a27a763b80e1d6eb5763b86c88e9e4e714"
 ],
 "trust_decision": {
  "summary": "Which server filesystem paths an agent tool (driven by a remote API/MCP user's prompt) may read is decided per tool: read_document has no check, read_file trusts an absolute run_dir as its sandbox root, and journal/shadow tools use safe_user_path whose envelope is all of HOME or CWD.",
  "evidence": [
   "agent/src/tools/doc_reader_tool.py:270",
   "agent/src/tools/read_file_tool.py:43-45",
   "agent/src/tools/path_utils.py:52-81",
   "agent/src/tools/trade_journal_tool.py:411",
   "agent/src/tools/shadow_account_tool.py:42-51",
   "agent/src/agent/loop.py:259-262"
  ]
 },
 "landing_point": {
  "where": "agent/src/tools/doc_reader_tool.py:270",
  "why": "Summary says 'file-read tools'; read_document takes an absolute file_path with no validation at all and is the most obvious reader."
 },
 "fix_sites": [
  {
   "where": "agent/src/tools/doc_reader_tool.py:270",
   "entry_point": "agent tool read_document (POST /sessions/{id}/messages -> AgentLoop; MCP read_document agent/mcp_server.py:238)",
   "module_kind": "tool implementation"
  },
  {
   "where": "agent/src/tools/read_file_tool.py:45",
   "entry_point": "agent tool read_file with LLM-supplied absolute run_dir (POST /sessions/{id}/messages; MCP read_file agent/mcp_server.py:290)",
   "module_kind": "tool implementation"
  },
  {
   "where": "agent/src/tools/path_utils.py:52-81",
   "entry_point": "agent tools analyze_trade_journal / extract_shadow_strategy / run_shadow_backtest / render_shadow_report via safe_user_path (agent/src/tools/trade_journal_tool.py:411, agent/src/tools/shadow_account_tool.py:51,94)",
   "module_kind": "shared path-validation helper (lower-level)"
  },
  {
   "where": "agent/src/tools/backtest_tool.py:21",
   "entry_point": "agent tool backtest(run_dir) reads run_dir/config.json",
   "module_kind": "tool implementation (generated-code tool)"
  },
  {
   "where": "agent/src/tools/pattern_tool.py:316",
   "entry_point": "agent tool pattern_recognition(run_dir) (MCP agent/mcp_server.py:205)",
   "module_kind": "tool implementation (analysis tool)"
  },
  {
   "where": "agent/src/tools/edit_file_tool.py:51",
   "entry_point": "agent tool edit_file with absolute run_dir (reads then writes)",
   "module_kind": "tool implementation"
  },
  {
   "where": "agent/src/tools/write_file_tool.py:49",
   "entry_point": "agent tool write_file with absolute run_dir",
   "module_kind": "tool implementation (write side, same run_dir root)"
  },
  {
   "where": "agent/api_server.py:745-801",
   "entry_point": "GET /runs, /runs/{id}, /runs/{id}/code, /runs/{id}/pine, /sessions*, /swarm/runs*, /shadow-reports/{id} gained require_auth (fix.diff:462-642)",
   "module_kind": "HTTP route auth (bundled, separate concern)"
  }
 ],
 "O1_entry_points": 9,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "agent/src/tools/path_utils.py:52-81 (safe_user_path, HOME \u222a CWD envelope, already called at agent/src/tools/trade_journal_tool.py:411 and agent/src/tools/shadow_account_tool.py:51,94)"
 },
 "O3_reason_to_dismiss": "The journal and shadow-account tools already call a dedicated path validator whose docstring says broker exports legitimately live anywhere in HOME, so a solver treats them as already protected and only patches read_document/read_file.",
 "O4_distance": {
  "files": 7,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Files uploaded via POST /upload are stored under agent/uploads and their absolute path is returned for the agent to read with read_document/analyze_trade_journal; read_file must keep read-only access to bundled skills/; SKILL.md examples use relative 'uploads/...' paths. Over-tight fixes (reject all absolute paths, run_dir-only) break these.",
  "where": "agent/api_server.py:1367; agent/api_server.py:1397; agent/src/tools/read_file_tool.py:46-49; agent/src/skills/doc-reader/SKILL.md:38"
 },
 "O6_input_shapes": [
  "absolute path",
  "relative path resolved against CWD",
  "../ traversal",
  "~ home expansion",
  "symlink (handled via resolve())",
  "UNC // or \\\\ prefix",
  "absolute LLM-supplied run_dir vs relative run_dir normalised by loop",
  "comma-separated env-configured extra roots"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "agent/src/agent/loop.py:240-262 (_normalize_tool_run_dir injects/keeps run_dir in tool args; absolute values pass through unchanged)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "factor_analysis tool reads LLM-supplied factor_csv/return_csv paths with pd.read_csv and no path check (and creates output_dir anywhere)",
   "where": "agent/src/tools/factor_analysis_tool.py:113-118",
   "reason_to_dismiss": "Returns only aggregated IC/IR statistics, not file contents, so it looks like an analysis tool rather than a 'file-read tool'; content leakage is limited to parse-error text.",
   "distance": "different tool module in agent/src/tools, same package as landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/agent/src/tools/factor_analysis_tool.py:37-38"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "agent/src/tools/factor_analysis_tool.py:117",
   "sibling": "Echo a preview of the first rows of factor_csv in the result for user sanity-checking",
   "why_realistic": "Analysis tools commonly show a data preview; makes the existing uncovered read a real content disclosure."
  },
  {
   "where": "agent/src/shadow_account/backtester.py:365",
   "sibling": "Let render_shadow_report/run_shadow_backtest accept a journal path from the cached profile metadata (save/reload) instead of re-validating kwargs",
   "why_realistic": "Profiles persist to ~/.vibe-trading/shadow_accounts; reusing the stored journal path for attribution is a natural convenience and would bypass the tool-level safe_user_path."
  },
  {
   "where": "agent/api_server.py:1367",
   "sibling": "A GET /uploads/{name} or document-preview route that reads UPLOADS_DIR / name",
   "why_realistic": "Frontend preview of uploaded files is a plausible feature next to the existing upload handler."
  }
 ],
 "O9_family": "path traversal / unrestricted file read (CWE-22/23, CWE-552) via agent tools",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (plus TypeScript frontend not needed)",
  "toolchain": "pip install -r agent/requirements.txt; pytest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "agent/tests/test_path_safety.py, agent/tests/test_doc_reader.py exist at pinned commit; fix adds test_doc_reader_security.py, test_file_tool_sandbox_security.py"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "agent/src/tools/path_utils.py, agent/src/tools/doc_reader_tool.py, agent/src/tools/read_file_tool.py, agent/src/tools/edit_file_tool.py, agent/src/tools/write_file_tool.py, agent/src/tools/backtest_tool.py, agent/src/tools/pattern_tool.py, agent/api_server.py (+ bundled shell-tool gating in agent/src/tools/__init__.py, agent/src/session/service.py, agent/src/swarm/*, agent/mcp_server.py, agent/cli.py, agent/backtest/runner.py)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a root check to read_document only (or reuse safe_user_path there), leaving the HOME-wide safe_user_path envelope and absolute run_dir in read_file/backtest/pattern tools untouched."
 },
 "out_of_scope_notes": [
  "GET /runs/{run_id}* build RUNS_DIR / run_id without validating run_id (agent/api_server.py:758,779,791); fix only adds auth there.",
  "Fix bundles unrelated hardening: shell-tool gating, upload extension blocklist, AST validation of signal_engine.py (fix.diff:654-772), loopback-only dev auth.",
  "cli.py cmd_upload reads any local path (agent/cli.py:1392) \u2014 local CLI, not a remote route."
 ],
 "unverified": [
  "pinned commit hash not supplied; taken as parent of the fix commit",
  "repo size in MB not measured (3526 files listed)",
  "whether FastAPI path params allow '..' to reach RUNS_DIR parent was not checked",
  "factor_analysis error message content exposure from pd.read_csv on non-CSV files not verified",
  "advisory text itself not provided; trust decision inferred from summary and diff"
 ]
}
  ```
- Published fix sites:   - agent/src/tools/doc_reader_tool.py:270 — entry point: agent tool read_document (POST /sessions/{id}/messages -> AgentLoop; MCP read_document agent/mcp_server.py:238) [tool implementation]
  - agent/src/tools/read_file_tool.py:45 — entry point: agent tool read_file with LLM-supplied absolute run_dir (POST /sessions/{id}/messages; MCP read_file agent/mcp_server.py:290) [tool implementation]
  - agent/src/tools/path_utils.py:52-81 — entry point: agent tools analyze_trade_journal / extract_shadow_strategy / run_shadow_backtest / render_shadow_report via safe_user_path (agent/src/tools/trade_journal_tool.py:411, agent/src/tools/shadow_account_tool.py:51,94) [shared path-validation helper (lower-level)]
  - agent/src/tools/backtest_tool.py:21 — entry point: agent tool backtest(run_dir) reads run_dir/config.json [tool implementation (generated-code tool)]
  - agent/src/tools/pattern_tool.py:316 — entry point: agent tool pattern_recognition(run_dir) (MCP agent/mcp_server.py:205) [tool implementation (analysis tool)]
  - agent/src/tools/edit_file_tool.py:51 — entry point: agent tool edit_file with absolute run_dir (reads then writes) [tool implementation]
  - agent/src/tools/write_file_tool.py:49 — entry point: agent tool write_file with absolute run_dir [tool implementation (write side, same run_dir root)]
  - agent/api_server.py:745-801 — entry point: GET /runs, /runs/{id}, /runs/{id}/code, /runs/{id}/pine, /sessions*, /swarm/runs*, /shadow-reports/{id} gained require_auth (fix.diff:462-642) [HTTP route auth (bundled, separate concern)]
- Uncovered routes to confirm (pattern B):   - agent/src/tools/factor_analysis_tool.py:113-118 — factor_analysis tool reads LLM-supplied factor_csv/return_csv paths with pd.read_csv and no path check (and creates output_dir anywhere) (reason to dismiss: Returns only aggregated IC/IR statistics, not file contents, so it looks like an analysis tool rather than a 'file-read tool'; content leakage is limited to parse-error text.; still in latest: yes)
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

## Environment (`tasks/vibe-trading-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/vibe-trading-ds/instruction.md`)
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

## Tests (`tasks/vibe-trading-ds/tests/`)
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
- **Wrong-fix patches** go in `build/vibe-trading-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/vibe-trading-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/vibe-trading-ds/manifest.json`:**
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

**Also in `build/vibe-trading-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py vibe-trading-ds --only static
python3 -I builder/gate.py vibe-trading-ds --only nop
python3 -I builder/gate.py vibe-trading-ds --only oracle
python3 -I builder/gate.py vibe-trading-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/vibe-trading-ds/`;
  - edit only `tasks/vibe-trading-ds/`, `build/vibe-trading-ds/` and, for pattern B, the register;
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
