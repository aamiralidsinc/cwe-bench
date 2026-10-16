# Pipeline: stage by stage

**Goal:** Harbor security-fix tasks that both DeepSeek V4.1 Flash (effort max) and MiMo-V2.6-Pro fail in all 3
attempts, where the failure is the model's fault and not the task's.
Run with `python run_pipeline.py` (see the [README](../README.md)). The state of each task is kept in
`data/pipeline_state.sqlite3`, so finished work is never repeated.

## Stage 1 - Mining

- **Sources:** OSV (bulk export), the GitHub Advisory Database (GHSA) and huntr. PyPI and npm only.
- **Fix commit:** taken from the advisory's commit links. A series of fix commits is merged; for a backport the
  default-branch copy is used. The commit before the fix is the vulnerable state.
- **Cutoff:** the advisory and the fix commit must be after `PUBLISHED_AFTER` (2026-08-01), so the fix is not in the
  models' training data.
- **Dedupe:** an advisory or commit already seen is never mined again.
- **Stored in:** `data/01_mined/osv_candidates.json`.

## Stage 2 - Screening

- **Rejected:**
  - dependency-bump, config, CI, docs and generated-only fixes;
  - template-dominated fixes;
  - no source change in Python or JS/TS;
  - fixes outside 4-400 source lines or over 300 files;
  - no root build manifest or no tests in the repo;
  - repos over 400 MB;
  - more than 3 candidates from one repo.
- **Score (fix breadth):** `8 × files (max 8) + 6 × (directories - 1, max 4)` + a line-band bonus, −25 for tiny
  fixes, +3 if the repo has 5+ tests. A small prior is added from how often the CWE broke both models before.
- **Stored in:** `data/02_screened/screened.json` (passed) and `rejected.json`.

## Stage 3 - Task builder

- **Picking candidates:**
  - screening score + a **learned adjustment** from results so far: vulnerability families that never broke a model
    rank lower, and so do packages already solved;
  - repos that cannot be built here or were safety-flagged are skipped;
  - one candidate per repo per batch.
- **Environment:** the repo is checked out at the vulnerable commit as a single snapshot commit, with no fix history.
  It is stored in `data/03_environments/<id>/repo/`, with the fix saved as `oracle_solution.patch`.
- **Build check:**
  - a Docker install of the project; the Python version comes from `requires-python` (3.11-3.13), and uv workspaces
    install from `uv.lock`;
  - network errors are retried;
  - a candidate whose build times out twice is retired.
- **Generation:** Claude Opus 5.5 gets the fix, the vulnerable source, its callers, a repo map, test examples and the
  knowledge base. It writes:
  - `instruction.md`: a behavioural bug report, 150-400 words, no file, function or line hints, no fix;
  - `hidden_tests.py`: ≥3 `test_security_*` (fail on the vulnerable code) and ≥3 `test_functional_*` (pass on both),
    through a real entry point, implementation-agnostic, offline, with variants beyond the report;
  - three check patches (shallow, removal, alternative) and metadata (entry point, techniques used).
- **Output checks:** no changed file or function names in the report, no copied advisory text, the minimum test
  counts, no skips (`skip`, `xfail`, `importorskip`), check patches that apply, output not truncated.
- **Fallbacks and safety:** if Opus 5.5 declines, Opus 4.8 continues. A safeguards (AUP) flag retires the candidate
  with no retry. A patch that is too large retires the candidate.

## Stage 4 - Validation

A task must pass all of these before any model sees it:

1. **Rubric:** 10 criteria, all blocking: accurate report, report doesn't prescribe the fix, solvable from the
   report, real entry point, variants share the root cause, implementation-agnostic, functional tests meaningful,
   deterministic and offline, realistic, not a config or dependency change.
2. **Recall probe:** both models get the report only; rejected if both name the file to fix.
3. **Leak checks:** the task files are audited, and the whole built image is scanned for copies of the fix's code
   (for example a released, already-fixed copy of the package in `node_modules`).
4. **Reference fix** scores 1.0 twice; the **vulnerable code** fails every security test.
5. **Existing repo tests** of the affected code pass before and after the fix. They are required, and enforced in
   grading.
6. **Check patches:** the *shallow* fix still fails a security test, the *removal* fix fails a functional test, and
   the *alternative* fix scores 1.0.

On failure the task goes back to stage 3 with the reviewer's or pytest's feedback (at most 2 rewrites). Docker or
infrastructure errors give "no verdict" and are retried. Records are kept in `data/03_environments/<id>/validation/`.

## Stage 5 - Evaluation (model runner)

- **Harness:** Harbor CLI 0.24 runs each task with the **Claude Code agent** (version pinned and baked into the task
  image). DeepSeek is reached through its Anthropic-compatible API with reasoning effort `max`, and MiMo through its
  own API.
- **Task image:** a `node:22` or `python:3.x-slim` base, the project installed (and built for TypeScript), the repo at
  the vulnerable commit, and Claude Code.
- **Blocked:**
  - **Network:** the agent container sits on an internal network; an egress proxy allows only the model API hosts.
    No GitHub, npm, PyPI or web search.
  - **Answer key:** no hidden tests, fix, fix history or advisory in the container.
  - **Credentials:** our Anthropic and GitHub keys are stripped from what Harbor passes into the container.
- **Grading in a separate container:** after the agent stops, only its source patch is collected (test configs and
  manifests excluded) and applied in a **fresh container** from the same image, where the hidden tests and the
  existing tests run. Nothing else the agent changed can reach the grader.
- **Score:** the mean of the security, functional and existing-test pass rates. Solved = 1.0; anything less is a
  failure (a partial fix or a broken feature).
- **Runs:** 3 attempts per model, 2 hours each, up to 5 tasks in parallel. Attempt 1 runs alone, then attempts 2-3
  together. Once either model solves, the remaining attempts are cancelled and the task is rejected.
- **Verdict (deterministic, no LLM judge):** **accepted** only if every attempt of both models is a counted failure
  (graded, below 1.0, no harness error, the agent really worked, no tampering). A **timeout is not a failure**.
- **Stored in:** `data/04_eval_runs/<id>/<model>/…`: each attempt's trajectory, patch and per-test results, plus
  `attribution.json`.

## Stage 6 - Packaging

- The reference fix runs one last time on the final task (it must score 1.0).
- **Harbor layout** written to `data/05_accepted_harbor/<id>/`: `instruction.md`, `task.toml` (CWE, language, repo,
  source, entry point, timeouts, network policy), `environment/` (Dockerfile + repo), `solution/` (reference fix),
  `tests/` (hidden tests, existing-test list, grader scripts).
- Run it with `harbor run -p data/05_accepted_harbor/<id> -a oracle`.

## Knowledge loop (after every verdict)

- **Rebuilt automatically:** `C_RESULTS.md` (all results and per-attempt failure details) and
  `data/knowledge/model_failure_map.md`.
- **Failure analyses:** `failure_analyses/<id>.md`, why each model failed, written from its trajectories.
- **Technique scoreboard:** `technique_scoreboard.md`, how often each design technique broke a model compared with
  the baseline.
- The **generator reads all of these** in the next round, and **candidate ranking** uses the same results.
