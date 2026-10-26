# vibe-trading-path-read — build notes (build-v1)

Start (UTC): see start_utc.txt (2026-10-17 06:24). End (UTC): 2026-10-17T07:46:00Z.

## Levers (one line each)
- T1 (A, landing): document reader takes any path; absolute, cwd-relative and `..`-out-of-uploads spellings.
- T2 (A, far / second implementation): shared broker-file validator admits all of HOME ∪ CWD; reached via the journal and shadow-profile tools. Dismiss: "already validated, docstring says HOME is legitimate".
- T3 (A + producer): workspace read/write/edit trust the model's run_dir; the agent loop's run_dir mapper passes absolute values through and resolves relative ones (so `../..` climbs out). Dismiss: "paths already confined to the workspace root".
- T4 (A): pattern scan and backtest take run_dir unchecked. Dismiss: "analysis/engine tools, not file readers".
- T5 (B, uncovered): factor analysis reads caller CSVs and mkdirs caller output_dir; untouched by the fix, still present on upstream main 596fcf3. Dismiss: "returns only aggregate statistics".
- T6/T7 (shapes): symlink inside uploads pointing out; sibling dir sharing a configured root's name prefix.
- Coupled must-keep-working: upload path → read/analyse; run workspace (relative `.`/subdir and absolute); bundled skills read; configured dirs (comma list, spaces, `~`); dot segments staying inside; backtest/pattern/factor on the current run. A project test pins the loop's absolute run_dir pass-through, so loop-level "drop it" fixes break a functional test.

## Verified
- Pinned = fd767f5, sole parent of fix 9454d4a; fix's regression tests absent at pinned.
- Locally (py3.11 venv, frozen versions = environment/constraints.txt): pinned 17/17 security fail, 16/16 hidden functional + 92 project testcases pass; oracle all pass; every checks/ patch behaves as declared (security_fail patches keep project tests green).
- T5 confirmed behaviourally on pinned (status ok with stats from a HOME CSV; output dir created outside).
- Entry point: AgentLoop.run with build_registry() and a scripted model stand-in; uploads via POST /upload (TestClient).

## Not verified / limits
- MCP transport not driven (same registry dispatch).
- Oracle omits the fix's bundled route-auth, shell gating, upload blocklist and runner AST checks (separate concerns).
- Out of scope noticed: GET /runs/{run_id}* build RUNS_DIR / run_id without validation (api_server.py:758,779,791); shell tool reads anything.
- First nop run failed: '~' on the document reader is not expanded at pinned (not an exploit); replaced by a '~' test on the broker-file tool.
- Gate: static ok (blind+FAIRNESS pending), nop ok (17 sec fail / 108 fun pass), oracle 3/3, patches 20/20 (one rerun after an infrastructure docker-network error).

## FAIRNESS revision (2026-10-17)
- Project set: TestNormalizeToolRunDir (and its `_normalize_tool_run_dir` import) dropped from the shipped test_loop_helpers.py; test_path_safety.py no longer shipped or run.
- Configured-directory tests (2 functional, 1 security sibling) now call the tool via `call_tool_fresh` (new interpreter, env set before import). Verified locally: an oracle variant that reads VIBE_TRADING_ALLOWED_FILE_ROOTS at import passes all tests.
- Instruction: prefix sentence removed; spelling list replaced by "whatever the path's spelling or wherever it ultimately resolves"; added the expected-project-test-failures sentence.
- Added security tests: run-storage sibling (`runs_<x>`) via the workspace reader (new check sf-prefix-run-storage.patch), and an upload-area link to a HOME broker file. Pinned now fails 19/19 security.
