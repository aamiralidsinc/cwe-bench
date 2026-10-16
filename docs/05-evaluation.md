# Stage 5 - Evaluation

Stage 5 is the pass@3 = 0 gate. Every task that stage 4 validated is run with Harbor (`harbor run`, CLI 0.24.0) against both target models: DeepSeek V4.1 Flash with reasoning effort `max`, and Xiaomi MiMo-V2.6-Pro. Both use Harbor's `claude-code` agent, pointed at each vendor's Anthropic-compatible API. The agent's container can reach only those two API hosts. Grading happens in a separate, fresh container that receives only the agent's source patch. A task is accepted only if every attempt of both models is a counted model failure. This is decided by deterministic code (`trial_analysis.attribute_attempt`, `model_runner.deterministic_verdict`). No LLM judge is involved. Optional LLM notes feed the knowledge base only (see [07-knowledge-loop.md](07-knowledge-loop.md)).

## Inputs and outputs

| What | Path / format |
|---|---|
| Tasks to run (input) | stage-4 `DONE` keys in `data/pipeline_state.sqlite3`; task dir `data/03_environments/<ID>/harbor_task/` (`TASK_DIRNAME`) built by `harbor_packager.build_task` in stage 4 |
| Per-attempt trial | `data/04_eval_runs/<ID>/<tag>/<tag>-<YYYYmmdd-HHMMSS>-{a,b}/<trial>/` with `config.json`, `result.json`, `trial.log`, `agent/` (`trajectory.json`, `claude-code.txt`), `artifacts/`, `verifier/` |
| Verifier files | `reward.txt`, `score_breakdown.json`, `ctrf.json`, `ctrf_existing.json`, `test-stdout.txt`, `agent.diff`, `agent_patch_{files,applied,dropped}.txt`, `agent_patch_apply.log`, `agent_changes.txt`, `outside_changes.txt`, `dependency_changes.txt`, `collect_error.txt` (on failure), `build.log` (npm) |
| Harbor console log | `data/04_eval_runs/<ID>/<tag>/harbor_stdout_{a,b}.log` (command line, exit code, stdout/stderr; keys are never on argv) |
| Task summary | `data/04_eval_runs/<ID>/summary.json` `{osv_id, status, detail, models{tag: expected, attempts[], passes, fails, errors, rewards, best_reward, model, jobs}}` |
| Attribution | `data/04_eval_runs/<ID>/attribution.json` `{timeout_policy, full_budget_sec, attempts{tag/job/trial: report}}` |
| Global summary | `data/04_eval_runs/summary.json` (all task summaries; `write_global_summary`) |
| Stage-6 oracle re-run | `data/04_eval_runs/<ID>/final_oracle/` (written by stage 6) |
| State | stage key `stage5_evaluator`: `done`, `failed`, `rejected_too_easy`, `accepted`, `rejected`, `needs_review` |
| Knowledge | `data/knowledge/task_outcomes.jsonl`, `results.md`, `ledger.md`, `C_RESULTS.md`, `skills/lessons_learned.md` |

`<tag>` is `deepseek` or `mimo` (`Config.eval_endpoints`).

## How it works

1. **Select** (`main`). `todo` = stage-4 `DONE` keys that `state.should_process(stage5, id, MAX_EVAL_TRIES=3)` allows: never seen, or `FAILED` fewer than 3 times. `pending` = stage-5 `DONE` keys that are still waiting for a verdict. `--only` filters both. `--dry-run` prints `todo` and exits.
2. **Preflight** (only when there is work). `cfg.eval_endpoints()` raises `ConfigError` if `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `MIMO_API_KEY` or `MIMO_MODEL` is missing. `harbor.preflight` checks that `harbor` and `docker` are on PATH and that `docker info` succeeds. `check_endpoint` sends one `POST {openai_base}/chat/completions` per model (`max_tokens: 8`, 90 s timeout). HTTP 401 or any non-200 response stops the stage.
3. **Budget**. `ContainerBudget(--max-containers or MAX_CONTAINERS)`. Task threads: `--workers`, or `max(2, budget)` if not set.
4. **Phase A** (`evaluate_task` -> `phase("a", 1)`). Attempt 1 of both models runs at once (one `run_harbor` per model in a 2-thread pool). The phase first acquires `len(endpoints) * max(1, min(k, budget // len(endpoints)))` slots, all or nothing.
5. **Early cancel** (`phase.watch`). Every 15 s the watcher reads both jobs' trials. If any trial has `reward >= 1.0`, it sets `cancel`. `run_harbor` polls every 5 s. On cancel it sends SIGINT (120 s grace), then SIGTERM (30 s), then kill (`_interrupt`). Running trials end as `CancelledError` and are ungraded.
6. **Decide** (`decide`, `attempt_outcome`). Any `pass` -> `REJECTED_TOO_EASY`. Any `error`, or fewer `fail`s than expected -> `FAILED`, which is retried on a later run. Otherwise -> `DONE`.
7. **Phase B**. Only if phase A gives `DONE` and `EVAL_ATTEMPTS > 1`. The remaining `EVAL_ATTEMPTS - 1` attempts of both models run with the same early cancel. Then `decide` runs again with `expected = EVAL_ATTEMPTS`.
8. **Tampered solves**. If the task is `REJECTED_TOO_EASY` but every passing attempt shows `tamper_signals`, the status becomes `NEEDS_REVIEW`.
9. **Record**. The stage writes `summary.json` and the state row. `knowledge.record_outcome` adds `model_verdicts`, `pattern` and `task_profile`. Optional LLM notes (unless `--skip-analysis`): `analyze_split` runs for patterns `only_*` or ones containing `_timed_out_`, and `analyze_solved` runs for `both_solve`.
10. **Verdict** (`finalize` -> `deterministic_verdict`). This runs for every stage-5 `DONE` task: after each task in follow mode, and for all of them after the pool finishes. It writes `attribution.json` and sets `ACCEPTED`, `REJECTED` or `NEEDS_REVIEW`.
11. **Knowledge**. `refresh_knowledge` (`failure_analyst.analyse` + `results_report.main`) runs per task. At the end of the run the stage also calls `knowledge.append_results`, `ledger.main`, `results_report.main` and `knowledge.update_lessons` (unless `--skip-lessons`). Finally it logs `docker system df`.

## Rules and techniques

### Harness and model access (`config.Config.eval_endpoints`, `harbor.run_harbor`)

| | DeepSeek | MiMo |
|---|---|---|
| Harbor agent | `claude-code` (`EVAL_AGENT`, or `<PREFIX>_AGENT`) | `claude-code` |
| `-m` | `anthropic/<model id>` (last `/` segment of `DEEPSEEK_MODEL`) | `anthropic/<model id>` |
| Anthropic base (`ANTHROPIC_BASE_URL`) | `https://api.deepseek.com/anthropic` | `https://api.xiaomimimo.com/anthropic` |
| Ping base (OpenAI-compatible) | `https://api.deepseek.com` | `https://api.xiaomimimo.com/v1` |
| `--ak` | `disable_web_search=true`, `reasoning_effort=max` | `disable_web_search=true` (no effort by default) |
| Egress allowlist host | `api.deepseek.com` | `api.xiaomimimo.com` |

- **Process env (secrets, never argv).** `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` (both = vendor key), `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`.
- **Agent env (`--ae`, non-secret).** `ANTHROPIC_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` are all set to the target model id, so no slot falls back to another model. Also `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` and `DISABLE_AUTOUPDATER=1`.
- **Credential stripping.** `run_harbor` drops every variable in `SENSITIVE_ENV` from the inherited environment, plus every variable ending in `_API_KEY` or `_AUTH_TOKEN`. `SENSITIVE_ENV` = `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `GITHUB_TOKEN`, `GH_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_BEARER_TOKEN_BEDROCK`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_BASE_URL`. Only the endpoint's own `extra_env` is added back. This keeps the pipeline's own Claude/Opus credentials out of the task container.
- **Command.** `harbor run -p <task> -a <agent> -o <jobs_dir> --job-name <name> -k <attempts> -n <concurrent> -y -q [-m ...] [--ak k=v]... [--ae k=v]...`.
- **Alternatives.** `<PREFIX>_AGENT=terminus-2` runs a host-side agent: the keys stay on the host and the container has no network. It uses `deepseek/<id>` or `openai/<id>`, and `<PREFIX>_CONTEXT_TOKENS` / `<PREFIX>_MAX_OUTPUT_TOKENS` become `model_info`. Any other agent name is passed through with `<PREFIX>_API_KEY` (for example Harbor's `mimo` agent).

### Task image (`harbor_packager.build_task`, built in stage 4)

- **Python** (`PY_DOCKERFILE`):
  1. `FROM python:<ver>-slim-bookworm`, then apt `git build-essential curl tmux asciinema`.
  2. `ENV SETUPTOOLS_SCM_PRETEND_VERSION=999.0.0 PBR_VERSION=999.0.0`, because the history is one snapshot commit.
  3. `pip install pytest==8.4.1 pytest-json-ctrf==0.3.5`.
  4. `WORKDIR /app`, `COPY repo/ /app/`, `pip>=25.1`.
  5. A uv workspace (`[tool.uv.workspace]` + `uv.lock`) is installed with `uv sync --frozen --inexact --all-packages --all-extras --all-groups` into `/usr/local` (`UV_WORKSPACE_INSTALL`). Otherwise `pip install -e ".[all,test,tests,testing,dev]"` is tried, then narrower fallbacks, then the groups `dev test tests testing`, then the known requirements files.
- **Python version** (`python_base_image`). Read from `requires-python`. The lower bound (`>=`, `~=`, `==`, or `>` + 1 minor) is used, never below 3.11 (`PY_MIN`) and capped at 3.13 (`PY_MAX`). An upper bound (`<` = minor - 1, `<=`) lowers it. No `requires-python` -> `python:3.11-slim-bookworm`.
- **Node** (`NODE_DOCKERFILE`):
  1. `FROM node:22-bookworm`, then apt `python3 python3-pip git build-essential tmux asciinema`, then pytest + ctrf (`--break-system-packages`).
  2. `NODE_INSTALL`: bun (version from `packageManager`), pnpm, yarn, or `npm ci || npm install`. Each tries the frozen lockfile first.
  3. `RUN (NODE_BUILD) || true`.
- **`NODE_BUILD`**. bun `run build`. For pnpm: the root `build` script if it exists, else `pnpm -r --if-present --no-bail run build`. yarn `run build`. Otherwise `npm run build --if-present`.
- **`NODE_REBUILD`**. Written to `tests/node_build.sh` and run by the grader. In a pnpm repo, it rebuilds only `--filter "[<image commit>]"`. In all other cases, or if that fails, it runs the full `NODE_BUILD`.
- **`CLAUDE_CODE_LAYER`**. Added when any endpoint uses `claude-code`, and inserted before `WORKDIR /app` so the layer is cached across tasks. It downloads `https://downloads.claude.ai/claude-code-releases/bootstrap.sh` (`curl --retry 5`), runs it with `CLAUDE_CODE_VERSION`, and symlinks `/usr/local/bin/claude`. Nothing is downloaded during the agent phase.
- **`MARKER_LAYER`** (the last layer). Commits the built `/app` (excluding `node_modules`) as `image build state`. Writes the commit to `/etc/.cwe_image_commit` and touches `/etc/.cwe_image_built`. That commit is the base of the agent's patch, and the marker file's timestamp is the cutoff for detecting changed files.
- **`Dockerfile.override`** (in the env dir). Replaces the base Dockerfile. It still gets the Claude Code layer, `TOOLS_LAYER` (tmux, asciinema) and `MARKER_LAYER`.

### Network isolation (`Config.agent_network_policy`, `PROXY_COMPOSE`, `docker/egress/egress.py`)

- **Default mode.** `proxy` when an in-container agent has API hosts, `no-network` for host-side agents. Set `AGENT_NETWORK` to override. `allowlist` selects Harbor's own nftables mode (Linux only).
- **Proxy mode** (`environment/docker-compose.yaml`). `main` is on `agent_isolated` (an `internal: true` network with no route out). `HTTP(S)_PROXY=http://egress:3128` and `NO_PROXY=localhost,127.0.0.1` are set. The `egress` service (image `cwe-egress:2`, `pull_policy: never`) joins `agent_isolated` plus the shared external network `cwe-egress-outside`. `ensure_egress_image` builds the image and the network once per machine.
- **Egress proxy** (`egress.py`):
  - Only `CONNECT` requests are allowed; anything else gets 405.
  - The host (lowercased) must be in `ALLOWED_HOSTS` and the port must be 443; otherwise 403.
  - The request line and the upstream connect each time out after 30 s.
  - TCP keepalive: idle 20 s, interval 10 s, count 9.
  - Every `ALLOW`, `DENY` and `CLOSE` (with byte counts) is printed to the container's docker logs.
- **No-network mode** (`OFFLINE_COMPOSE`). `main` gets `network_mode: none`. In both compose modes, `task.toml` leaves Harbor's own `network_mode` unset.

### Separate grader (`render_task_toml`, `COLLECT_SH`, `TEST_SH`, `SCORE_PY`)

- **`[verifier] environment_mode = "separate"`.** Grading runs in a fresh container built from the same image.
- **Collect.** `[[verifier.collect]]` (300 s) runs `COLLECT_SH` in the agent's container when the agent stops. It writes to `/logs/artifacts/`:
  - `agent.patch`: `git diff --cached --binary --no-renames <image commit>`, excluding `node_modules`.
  - `agent_changes.txt` (name and status of each changed file).
  - `outside_changes.txt`: files newer than the marker outside `/app`, `/proc`, `/tmp`, `/root` and the other pruned paths, up to 500 entries.
  - `dependency_changes.txt`: files in `node_modules` newer than the marker, up to 200 entries.
  - `collect_error.txt`, if the diff failed.
- **`TEST_SH` steps.**
  1. Copy the records into `/logs/verifier`. Apply the patch with `git apply --binary` and exclude every `GRADER_EXCLUDES` file. On failure it writes `APPLY FAILED` and retries with `--reject`. It records `agent_patch_{files,applied,dropped}.txt`.
  2. Run `node_build.sh` if present (600 s).
  3. Run the hidden tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest /tests/test_outputs.py -p ctrf.main -p no:cacheprovider --rootdir=/app -c /dev/null --confcutdir=/tests` (900 s).
  4. Restore `/tests/existing_snapshot/` over `/app`, then run the existing tests (900 s) with `existing_node.py` (npm) or pytest -> `ctrf_existing.json`.
  5. Run `score.py`.
- **`GRADER_EXCLUDES`**: `conftest.py pytest.ini tox.ini setup.cfg pyproject.toml package.json package-lock.json yarn.lock pnpm-lock.yaml bun.lock bun.lockb sitecustomize.py usercustomize.py *.pth vitest.config.* vite.config.* jest.config.* jest.setup.* karma.conf.* .mocharc*`.
- **Score** (`score.py`). Parts: `security` = fraction of passing `test_security_*` tests, `functional` = fraction of passing `test_functional_*` tests, and `existing` = fraction of `existing_expected.txt` names that passed, where a missing name counts as failed. `existing` is included only if that list is non-empty. If there is no `ctrf.json`, the only part is `hidden` (1.0 if the pytest return code is 0, else 0.0). The reward is `1.0` only if every part is 1.0; otherwise it is `min(mean(parts), 0.99)`. It is written to `reward.txt` (`%.4f`) and `score_breakdown.json`.
- **Verifier budget.** `VERIFY_BUDGET_SEC` = 600 + 900 + 900 + 300 = 2700 s.

### Attribution and verdict (`trial_analysis.attribute_attempt`, `model_runner.deterministic_verdict`)

- **`attempt_outcome`.** `pass` if reward >= 1.0. `error` if there is no reward, or if the attempt raised an exception other than `AgentTimeoutError`. Otherwise `fail`.
- **When an attempt is counted.** It is counted only if it is not solved and its problem list is empty. The possible problems:
  - **Ungraded.** No reward.
  - **Per-test report.** `ctrf.json` is missing, or does not contain every `test_security_*` / `test_functional_*` name found by parsing (AST) `tests/test_outputs.py`.
  - **Exception.** A non-timeout exception.
  - **Timeout.** Any timeout under `exclude` (`TIMEOUT_NOT_COUNTED`). Under `count`, a timeout whose budget (parsed from "after N seconds") is below `FULL_BUDGET_SEC`.
  - **Too few turns.** Fewer than `MIN_AGENT_STEPS = 3` agent turns in `trajectory.json`.
  - **Tampering.** `tamper_signals` finds any hit.
  - **Grader problems.** With a separate grader, `grader_problems` reports a `collect_error.txt`, `APPLY FAILED`, or dropped manifests (`MANIFESTS`) on an unsolved attempt.
- **`tamper_signals`.** `TAMPER_CMD_RE` is matched against every tool-call argument, catching `/tests`, `/logs/verifier`, `reward.txt`, `score_breakdown.json` and `ctrf(_existing).json`. Older shared-container tasks are also checked for edits to test-runner config (`TAMPER_FILE_RE`), writes outside the repo (`TAMPER_OUTSIDE_RE`), and dependency changes. At most 5 hits are kept.
- **Failure classes** (`classify_attempt`, from `score_breakdown.json` parts, where a missing part = 1.0). `hole_still_open` (security < 1, everything else 1), `over_correction` (security 1, something else < 1), `hole_open_and_broke_features` (both), otherwise `unknown`. A partial fix is a failure.
- **Verdict.** `ACCEPTED`: every model has `expected` counted failures and there are no problems. `REJECTED`: the only uncounted attempts are pure `TIMEOUT_NOT_COUNTED` ones. `NEEDS_REVIEW`: anything else, with the reasons (detail truncated to 600 characters). `--reverdict <ID> [--apply]` re-runs this logic on the recorded trials. `--apply` writes the state, resets stage 6, and calls `unpublish` for tasks that are not accepted.

### Timeouts and containers

- **Time limits.** Per-attempt agent limit = `AGENT_TIMEOUT_SEC`, written into `task.toml`. The Harbor subprocess deadline is `waves * (AGENT_TIMEOUT_SEC + 2700) + 1800` s, where `waves = ceil(k / concurrent)`. Exceeding it raises `TimeoutExpired`, and the task is marked `FAILED`.
- **`TIMEOUT_POLICY`.** `exclude` (default; the agreed rule) means a timeout is never a model failure. `count` counts a timeout only at `>= FULL_BUDGET_SEC` (7000).
- **Concurrency per model.** `max(1, min(k, budget // n_models))`. With the defaults (budget 4, 2 models, 3 attempts), phase A takes 2 slots and phase B takes 4. Slots count trials only. Each trial's egress-proxy and verifier containers are not counted.
- **Cleanup** (`remove_job_containers`). Runs after every `harbor run`, including cancelled and timed-out ones. It does `docker rm -f` on every container whose compose project label starts with a lower-cased trial directory name, then `docker network rm` on the networks that match.

### What is blocked

| Threat | Prevention |
|---|---|
| Web lookup of the fix | `disable_web_search=true`. The egress allowlist has only the model API hosts. Telemetry and auto-update are off. |
| Leaked host credentials | `SENSITIVE_ENV` and `*_API_KEY` / `*_AUTH_TOKEN` are stripped before `harbor run` |
| Editing tests or grader inputs | Fresh grader container. Only the source patch is applied, minus `GRADER_EXCLUDES`. Plugin autoload is off and `-c /dev/null` is passed. Existing tests are restored from the snapshot. A solve with only tampered passes -> `NEEDS_REVIEW` |
| Answer keys in the image | `tests/` and `solution/` are not in the build context (`audit_task` allows only `Dockerfile`, `repo/`, `docker-compose.yaml`). One snapshot commit. Stage-4 image scan (`scan_image_for_fix`). Pinned SCM versions. The uv lock is used instead of released copies. |
| Infra noise counted as model failure | Ungraded runs, exceptions, timeouts, too few turns and grader apply problems are all uncounted |

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `MIMO_API_KEY`, `MIMO_MODEL` | required | endpoints |
| `<PREFIX>_ANTHROPIC_BASE_URL` / `<PREFIX>_BASE_URL` | vendor URLs above | Anthropic API base / ping base |
| `<PREFIX>_REASONING_EFFORT` | DeepSeek `max`, MiMo empty | `--ak reasoning_effort` |
| `EVAL_AGENT` / `<PREFIX>_AGENT` | `claude-code` | Harbor agent |
| `EVAL_ATTEMPTS` | 3 | attempts per model |
| `MAX_CONTAINERS` / `--max-containers` | 4 | container budget |
| `AGENT_TIMEOUT_SEC` | 3600 (code default; the shipped task has `7200.0`) | agent limit in `task.toml` |
| `TIMEOUT_POLICY`, `FULL_BUDGET_SEC` | `exclude`, 7000 | timeout rule |
| `AGENT_NETWORK` | derived | force `proxy` / `allowlist` / `no-network` / `public` |
| `CLAUDE_CODE_VERSION` | empty | version passed to `bootstrap.sh` |
| `TASK_CPUS`, `TASK_MEMORY_MB` | 2, 3072 | `[environment]` |
| `HARBOR_BIN` | venv `harbor`, else PATH | |
| `--only`, `--dry-run`, `--skip-analysis`, `--skip-lessons` | | via `run_pipeline.py --stage 5` |
| `--follow` (+ `--workers`, default 4 in `run_pipeline.py`) | off | start tasks as stage 4 validates them. Polls every `--follow-poll` 60 s and stops when no `run_pipeline.py` process with `--stage 3`, `--stage 4` or `--to-stage 4` is running (`upstream_running`) |
| `--skip-api-check`, `--model`, `--follow-poll` | | only via `python -m src.stage5_evaluator.model_runner` (not forwarded by `__init__.run`) |
| `--reverdict ID... [--apply]` | | `run_pipeline.py` |

## Code map

| File | Key functions |
|---|---|
| `src/stage5_evaluator/model_runner.py` | `main` (selection, pools, follow mode), `evaluate_task` (phases, early cancel), `decide`, `attempt_outcome`, `deterministic_verdict`, `finalize`, `reverdict`, `ContainerBudget`, `check_endpoint`, `refresh_knowledge` |
| `src/stage5_evaluator/trial_analysis.py` | `attribute_attempt`, `tamper_signals`, `grader_problems`, `classify_attempt`, `hidden_test_names`; LLM notes `analyze_split` / `analyze_solved` |
| `src/common/harbor.py` | `run_harbor` (command, env stripping, cancel), `_interrupt`, `remove_job_containers`, `read_trial(s)`, `Trial.timed_out` |
| `src/common/config.py` | `Config.load`, `eval_endpoints`, `agent_network_policy`, `preinstall_claude_code` |
| `src/stage6_packager/harbor_packager.py` | `build_task`, `python_base_image`, Dockerfile / compose / `TEST_SH` / `SCORE_PY` / `COLLECT_SH` constants, `ensure_egress_image` |
| `docker/egress/egress.py` | `handle` (CONNECT allowlist), `keepalive` |

## Known limitations

- **Defaults disagree.** The `AGENT_TIMEOUT_SEC` code default (3600) is below `FULL_BUDGET_SEC` (7000), so under `count` a timeout with default settings is never counted. The shipped task uses 7200, so the value must come from the environment. `C_RESULTS.md` hardcodes "2-hour".
- **`AGENT_NETWORK=proxy` fails.** Forcing `proxy` explicitly returns an empty host list (`agent_network_policy` passes hosts only for `allowlist`), and `build_task` then raises "proxy network mode needs the model-API hosts".
- **Grader network in proxy mode is unverified.** In proxy mode the code does not set a network for the separate verifier container. Whether Harbor applies the same compose file (and so the same allowlist) to it was not checked here.
- **Unverified Harbor behaviour.** The mapping of `disable_web_search` / `reasoning_effort` to Claude Code options is inside Harbor's agent and was not checked here. The same goes for "Harbor uploads `tests/` only after the agent finished", which is stated in the `harbor_packager` docstring.
- **Phase-A errors cost a retry.** A phase-A error marks the task `FAILED` without running phase B. It is retried up to 3 times, and each retry starts a new run id.
- **The budget can be overcommitted.** If the budget is smaller than the number of models, a phase still runs 1 trial per model, which is more than the budget.
- **One status is never assigned.** `REJECTED_TASK_DEFECT` exists in `Status` but stage 5 never sets it.
- **`--skip-analysis` is partial.** It does not skip `failure_analyst.analyse`. `refresh_knowledge` always calls it, and it makes an LLM call whenever a model has a counted failure.
