# Stage 6 - Packaging

Stage 6 ships the tasks that stage 5 accepted. It does not build a new task. It copies the exact Harbor task directory that stage 4 built and validated, and that stage 5 evaluated (`data/03_environments/<ID>/harbor_task/`). It re-runs the oracle on that copy and, if the copy still scores 1.0, moves it to `data/05_accepted_harbor/<id>/` and records the task's provenance. The validated artifact and the shipped artifact are therefore the same bytes (`harbor_packager` module docstring). This document also describes the layout `build_task` produces, because that is what ships.

## Inputs and outputs

| What | Path / format |
|---|---|
| Tasks to package (input) | stage-5 `ACCEPTED` keys in `data/pipeline_state.sqlite3`, filtered by `state.should_process("stage6_packager", id)` (default max 3 tries) |
| Source task | `data/03_environments/<ID>/harbor_task/` (`TASK_DIRNAME`) |
| Metadata | `data/01_mined/osv_candidates.json`, overlaid by `data/02_screened/screened.json` (`load_meta`) |
| Staging copy | `data/05_accepted_harbor/<id>.building/` (removed on failure; git-ignored) |
| Final oracle run | `data/04_eval_runs/<ID>/final_oracle/final-<unix time>/<trial>/` |
| Shipped task (output) | `data/05_accepted_harbor/<id>/`, where `<id>` is the lower-cased OSV id |
| Provenance (output) | `data/05_accepted_harbor/provenance.json` |
| State | stage key `stage6_packager`: `DONE` with payload `{"dir": <id>}`, or `FAILED` with the error |

## How it works

1. **Select** (`package_accepted`). Stage-5 `ACCEPTED` ids. `--only` filters them. Ids already `DONE` in stage 6 are skipped. If nothing is left, the stage returns 0.
2. **Preflight**. Unless `--skip-final-oracle` is set, `harbor.preflight` checks harbor, docker and `docker info`. On failure the stage exits 1 and suggests `--skip-final-oracle`.
3. **Copy**. `shutil.copytree(src, <id>.building, symlinks=True, copy_function=shutil.copy2)`. This is a real copy, not hardlinks, so later edits to stage-3 files can never change a shipped task.
4. **Final oracle run**. `run_harbor(harbor, staging, "oracle", data/04_eval_runs/<ID>/final_oracle, "final-<unix time>", timeout=3600)`, with `run_harbor`'s defaults `-k 1 -n 1`. The run must produce at least one trial, and every trial must have `reward == 1.0`. Otherwise `PackagingError("final oracle run did not score 1.0: ...")`.
5. **Publish**. Remove the old `<id>/` and `os.replace(staging, dest)`.
6. **Provenance**. `provenance[OSV-ID] = {cve_id, repo_url, pre_patch_commit, fixed_commit, ecosystem, package, cwe_ids, summary, task_dir}`.
7. **State**. `DONE` with `{"dir": <id>}`. On `PackagingError`, `OSError` or `HarborUnavailable`, the stage marks `FAILED`, deletes the staging dir and continues with the next task.
8. **Write provenance.json** atomically (`.tmp` then `replace`). The return code is 1 if any task failed.

**Withdrawal** (`unpublish`, called by `run_pipeline.py --reverdict <ID> --apply` when the new verdict is not `ACCEPTED`). It moves `<id>/` to `data/knowledge/archive/rejected_tasks/<id>/` and removes the entry from `provenance.json`. A re-verdict that gives `ACCEPTED` resets the stage-6 state, so the next stage-6 run packages the task again.

## Rules and techniques

### Task layout (`build_task`, written in stage 4)

| Path | Content / rule |
|---|---|
| `task.toml` | `render_task_toml` (see below) |
| `instruction.md` | Copy of the env's `instruction.md` (the bug report the agent sees) |
| `environment/Dockerfile` | `PY_DOCKERFILE` / `NODE_DOCKERFILE` / `Dockerfile.override`, plus `CLAUDE_CODE_LAYER` (claude-code endpoints) and `MARKER_LAYER`. See [05-evaluation.md](05-evaluation.md) |
| `environment/docker-compose.yaml` | `PROXY_COMPOSE` (proxy mode: egress `cwe-egress:2`, `ALLOWED_HOSTS: api.deepseek.com,api.xiaomimimo.com`) or `OFFLINE_COMPOSE` (no-network). Absent for `allowlist` / `public` |
| `environment/repo/` | Pre-patch checkout copied with hardlinks where possible (`_link_or_copy`). Symlink cycles are dropped (`drop_cyclic_symlinks`). One snapshot commit in `.git` |
| `solution/solve.sh` | `git apply --whitespace=nowarn oracle_solution.patch` in `/app` (`SOLVE_SH`) |
| `solution/oracle_solution.patch` | The human fix with the per-file chunks for test files removed (`split_patch_without_tests`). A patch with only test changes is an error |
| `tests/test.sh` | `TEST_SH` (apply the agent's patch, rebuild, hidden tests, existing tests, score). Executable |
| `tests/score.py` | `SCORE_PY`, the partial score; 1.0 only if every part passes |
| `tests/test_outputs.py` | Copy of `hidden_tests.py` |
| `tests/existing_files.txt` | Up to `MAX_EXISTING_FILES = 15` repo test files that touch the fix (`select_existing_tests`). Paths matching `playwright\|e2e\|selenium\|cypress\|benchmark\|integration` are skipped; scanned candidate files over 300 KB are ignored |
| `tests/existing_expected.txt` | The pass->pass test names that stage 4 derived (`oracle_runner.derive_existing_expected`) |
| `tests/existing_snapshot/` | Pristine copies of those test files, plus every `conftest.py` / `__init__.py` above them, plus the `TEST_RUNNER_CONFIGS` files (root `pytest.ini`, `tox.ini`, `conftest.py`; `vitest.config.*` up to two levels deep; `jest.config.*` and `.mocharc*` up to one level; never inside `node_modules`, `dist` and the other `JS_SKIP_DIRS`) |
| `tests/snapshot_commit.txt` | `git rev-parse HEAD` of the repo snapshot |
| `tests/node_build.sh` | npm only: `cd /app` + `NODE_REBUILD` |
| `tests/existing_node.py` | npm only: runs each existing file with vitest / jest / mocha / `node --test` (300 s per file) -> `ctrf_existing.json` |

`audit_task` (stage 4) rejects a task if `environment/` contains anything other than `Dockerfile`, `repo/` and `docker-compose.yaml`, or if the Dockerfile has a `COPY`/`ADD` other than `COPY repo/ /app/`.

### `task.toml` (`render_task_toml`)

```toml
schema_version = "1.1"
[task]
name = "cwe-bench/<id lower>"
description = "Fix a security vulnerability (CWE-79)"     # CWEs appended when known
keywords = ["security", "code-vulnerability", "common-weakness-enumeration", "cwe-79"]
[metadata]
category = "security"
difficulty = "hard"
tags = ["security", "<ecosystem lower>", "cwe-79"]
cwe_ids = ["CWE-79"]
language = "javascript"            # python | typescript | javascript (results_report.language), else "unknown"
repo = "https://github.com/<owner>/<repo>"
source = "mined:ghsa+osv"          # "mined:" + sources joined by "+", default ["osv"]
entry_point = "..."                # from <env>/task_metadata.json
[agent]
timeout_sec = 7200.0               # AGENT_TIMEOUT_SEC (code default 3600)
# network_mode / allowed_hosts only when the mode is not compose-enforced (allowlist / public)
[verifier]
timeout_sec = 2700.0               # VERIFY_BUDGET_SEC
environment_mode = "separate"
# network_mode = "no-network" only when the mode is not compose-enforced
[[verifier.collect]]
command = "bash -c '<COLLECT_SH>'"
timeout_sec = 300.0
[environment]
build_timeout_sec = 1200.0
cpus = 2                           # TASK_CPUS
memory_mb = 3072                   # TASK_MEMORY_MB
storage_mb = 10240
```

Values above are from the shipped `ghsa-hxh3-vqpv-xpqv/task.toml`. Commit hashes, the CVE id and the OSV summary are deliberately left out of `task.toml`, because they would let an agent look the fix up. They are kept only in `provenance.json`.

### `provenance.json`

One object keyed by OSV id (original case). Each entry has: `cve_id`, `repo_url`, `pre_patch_commit`, `fixed_commit`, `ecosystem`, `package`, `cwe_ids`, `summary`, `task_dir`. It is the only place that links a shipped task to its upstream fix. Keep it out of anything you give an agent.

### Running a packaged task with Harbor

Prerequisites for a proxy-mode task (the default with `claude-code`): the egress image and the outbound network must exist locally, because the compose file uses `pull_policy: never`. This is what `ensure_egress_image` does:

```bash
docker build -t cwe-egress:2 docker/egress
docker network create cwe-egress-outside
```

Oracle check (the same call stage 6 makes):

```bash
harbor run -p data/05_accepted_harbor/<id> -a oracle -o /tmp/jobs --job-name oracle-check -y
```

A target-model run with the same flags stage 5 uses. Put the key in the environment, never on argv:

```bash
ANTHROPIC_API_KEY=<key> ANTHROPIC_AUTH_TOKEN=<key> ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \
ANTHROPIC_MODEL=<model-id> harbor run -p data/05_accepted_harbor/<id> -a claude-code -m anthropic/<model-id> \
  -k 3 -n 2 --ak disable_web_search=true --ak reasoning_effort=max \
  --ae ANTHROPIC_MODEL=<model-id> --ae ANTHROPIC_SMALL_FAST_MODEL=<model-id> \
  --ae CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 --ae DISABLE_AUTOUPDATER=1 \
  -o /tmp/jobs --job-name ds-check -y
```

Stage 5 also sets `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` (see [05-evaluation.md](05-evaluation.md)). Harbor leaves sidecar containers running after a job. The pipeline removes them with `harbor.remove_job_containers`; a manual run should do the same.

### What is (not) committed to git (`.gitignore`)

| Path | In git |
|---|---|
| `data/05_accepted_harbor/<id>/` (task.toml, instruction.md, Dockerfile, compose, solution/, tests/) | yes |
| `data/05_accepted_harbor/*/environment/repo/` | no: the snapshot has its own `.git`, so git would store only a pointer. Share full tasks as zips |
| `data/05_accepted_harbor/*.building/` | no |
| `data/05_accepted_harbor/provenance.json` | yes (not ignored) |
| `data/03_environments/`, `data/04_eval_runs/` (including `final_oracle/`) | no |
| `data/logs/`, `data/.cache/`, `data/*.sqlite3*`, `data/state.db`, `data/knowledge/archive/` | no |
| `.env`, `.env.*` (except `.env.example`), `share/`, `others/`, `cwe-bench/`, `*.zip`, `positive-findings.txt` | no |

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `--only ID...` | all accepted | restrict to these OSV ids (`run_pipeline.py --stage 6 --only ...`) |
| `--skip-final-oracle` | off | package without the final `harbor run -a oracle` |
| `HARBOR_BIN` | venv `harbor`, else PATH | Harbor binary |
| `CWE_DATA_DIR` / `--data-dir` | `./data` | data root |
| `AGENT_TIMEOUT_SEC`, `TASK_CPUS`, `TASK_MEMORY_MB`, `AGENT_NETWORK`, `CLAUDE_CODE_VERSION` | 3600, 2, 3072, derived, empty | used when stage 4 runs `build_task`. Stage 6 does not rebuild, so changing them has no effect on an already-built task |

## Code map

| File | Key functions |
|---|---|
| `src/stage6_packager/__init__.py` | `run`: forwards `--only` / `--skip-final-oracle` to `harbor_packager.main` |
| `src/stage6_packager/harbor_packager.py` | `package_accepted` (stage-6 loop), `build_task` (layout), `render_task_toml`, `split_patch_without_tests`, `select_existing_tests(_js)`, `drop_cyclic_symlinks`, `audit_task`, `scan_image_for_fix`, `unpublish`, `load_meta`, `ensure_egress_image` |
| `src/common/harbor.py` | `run_harbor`, `read_trials`, `preflight` |
| `src/stage5_evaluator/model_runner.py` | `reverdict` (re-queue or withdraw a packaged task) |
| `src/stage4_oracle_validator/oracle_runner.py` | calls `build_task` / `audit_task` / `scan_image_for_fix`; writes `existing_expected.txt` |

## Known limitations

- **Single oracle trial.** The final oracle run uses one trial (`-k 1`), so a flaky oracle can pass once. Stage 4 runs the oracle `--oracle-repeats` times, which that stage's documentation covers.
- **No re-audit.** Stage 6 does not re-run `audit_task` or the image scan. It relies on stage 4 and on the copy being byte-identical.
- **Machine-specific prerequisites.** Shipped proxy-mode tasks depend on `cwe-egress:2` and `cwe-egress-outside` existing on the host that runs them. Docker Desktop for Mac cannot use Harbor's nftables allowlist, which is why proxy mode exists (`config.agent_network_policy`).
- **Repo not in git.** A clone of the repo does not contain `environment/repo/`, so a packaged task cannot be run from git alone.
- **Old copy kept on failure.** If re-packaging fails, the previously shipped `<id>/` and its provenance entry stay in place. Only the staging dir is removed, because `dest` is replaced only after the oracle passes.
- **Unused default.** `build_task`'s own `agent_timeout` default (1800) is never used: stage 4 always passes `AGENT_TIMEOUT_SEC`.
