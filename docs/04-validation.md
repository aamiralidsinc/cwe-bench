# Stage 4 - Oracle validator

Stage 4 proves that each generated task is fair and actually tests the bug, before any target-model budget is spent. The checks run in this order:

1. An LLM rubric review.
2. A text-only recall probe against the two target models.
3. The task is packaged as a Harbor task, and the task directory and the built image are audited for answer-key leaks.
4. The task is run in Docker:
   - the human fix must score 1.0 on every run;
   - the untouched vulnerable code must fail every security test and pass every functional test;
   - the repo's own related tests must pass before and after the fix;
   - three generated check patches (shallow, removal, alternative) must produce the expected outcomes.

Defects that a regenerated task can fix are sent back to stage 3 with concrete feedback, up to a limit. Everything else ends in a terminal status or a retryable no-verdict.

## Inputs and outputs

| What | Path / format |
|---|---|
| Task (input) | `data/03_environments/<OSV-ID>/` with `oracle_solution.patch`, `instruction.md`, `hidden_tests.py` (`REQUIRED_FILES`, `discover`); plus `task_metadata.json`, `check_patches/*.patch`, `repo/` |
| Candidate metadata | `screened.json` / `osv_candidates.json` via `harbor_packager.load_meta`; the ecosystem must be `PyPI` or `npm` (`build_task`) |
| Rubric verdict | `<env>/rubric_check.json` `{passed, criteria, blocking_issues}` (`rubric_check.check_task`) |
| Recall probe | `<env>/recall_probe.json` `{targets, models, risk}` (`recall_probe.probe`) |
| Harbor task | `<env>/harbor_task/` (`task.toml`, `instruction.md`, `environment/`, `solution/`, `tests/`) (`build_task`) |
| Isolation audit | `<env>/isolation_audit.json` `{issues, image_scanned[, scan_error]}` |
| Harbor runs | `<env>/validation/<name>-<stamp>/` and `.log`; check-patch task copies in `validation/check_tasks/<kind>/` |
| Pass->pass set | `harbor_task/tests/existing_expected.txt` (one test name per line) |
| Verdict | `<env>/oracle_validation.json` `{osv_id, ok, detail, data, at}`; state key `stage4_oracle_validator` |
| Regeneration archive | `<env>/attempts/round_N/` (previous files + `execution_feedback.txt`) |
| Knowledge | `task_outcomes.jsonl` rows (`validated`, `recall_probe`, failure status); a run table appended to `data/knowledge/results.md` |

## How it works

`oracle_runner.main` picks every discovered task for which `should_process(STAGE, id, MAX_NO_VERDICT=2)` is true. It runs `harbor` preflight (the binary exists and `docker info` succeeds), then calls `validate_task` with up to `min(--workers, 3)` tasks in parallel.

1. **Rubric** (`rubric_check.check_task`).
   - An earlier pass is reused if `rubric_check.json` passed and is not older than `instruction.md` / `hidden_tests.py`.
   - A failure returns `REJECTED_RUBRIC`.
   - This step is skipped with `--skip-rubric`.
2. **Recall probe** (`recall_probe.probe`). It is skipped with `--skip-probe`.
   - Risk `high` with `--probe-reject` (on by default) gives `REJECTED`.
   - Any exception (for example, missing model credentials) only logs a warning, and validation continues.
3. **Package** (`build_task`) into `harbor_task/`. A `PackagingError` is terminal (`FAILED_ORACLE`).
4. **Static isolation audit** (`audit_task`). Any issue is terminal.
5. **Image fix scan** (`scan_image_for_fix`). It runs only if the audit is clean and `--skip-image-scan` is not set.
   - `ImageScanUnavailable` means no verdict.
   - Any hit is terminal.
6. **Oracle**: `harbor run -a oracle -k --oracle-repeats` (default 2), checked by `check_oracle`.
7. **Pre-patch**: `harbor run -a nop -k 1`, checked by `check_pre_patch`.
8. **Existing tests** (`derive_existing_expected`). The pass->pass set is written to `existing_expected.txt`.
   - If the set is non-empty, an extra `oracle-final` run (k=1) must score 1.0 with the set enforced.
   - If the set is empty and `--require-existing` is in effect, the task is terminal "out of spec".
9. **Fix checks** (`run_fix_checks` → `check_fix_patches`). This step is skipped with `--skip-fix-checks`.
10. **Record** (`process`): writes `oracle_validation.json` and an outcome row, then routes the verdict as shown in the outcome table.

Harbor timeouts: `per_run = VERIFY_BUDGET_SEC + 1500 = 4200 s`, where `VERIFY_BUDGET_SEC = 600 + 900 + 900 + 300`.
- Each `harbor run` gets `max(--timeout, k * per_run)` (8,400 s for the 2-trial oracle).
- Each fix-check run gets `max(--timeout, per_run)`.

## Rules and techniques

**Rubric** (`rubric_check.CRITERIA`)
- How the review is run:
  - Model: `--model` (default `ANTHROPIC_MODEL`), via `CliBackend` with a 900 s timeout and 8,000 max tokens.
  - The reviewer sees the instruction, the tests, the oracle patch without test files (`split_patch_without_tests`, ≤ 60,000 characters) and the entry point.
  - If the reply has no parseable JSON object, the call is repeated once with `GEN_FALLBACK_MODEL` (default `claude-opus-4-8`).
- All 10 criteria are currently critical, so any `pass: false` or unanswered criterion blocks (`evaluate_reply`):

| Criterion | Passes when |
|---|---|
| `no_hints` | the report names no file/module/path/line/changed function or class, and does not prescribe the fix design |
| `accurate_report` | it describes the vulnerability the oracle actually fixes |
| `solvable_from_report` | every tested behaviour can be derived from the report + code |
| `real_entry_point` | security tests go through a public API/route/CLI, not the edited internal function |
| `variants_share_root_cause` | variants share the root cause and are all blocked by the oracle |
| `implementation_agnostic` | no imports/asserts of patch additions, no exact error text, any reasonable blocking is accepted |
| `functional_meaningful` | functional tests would fail if the feature were removed or over-blocked, and pass on vulnerable code |
| `deterministic_offline` | no network, no timing races, no result-flipping randomness |
| `realistic` | a realistic use of the project |
| `security_not_trivial_config` | the bug is in program logic, not a dependency bump or config toggle |

**Recall probe** (`recall_probe.py`)
- One chat completion per target endpoint. It goes to `<check_url>/chat/completions` (OpenAI-compatible), with `max_tokens` 3000 and a 180 s timeout. The model sees the report only.
- What counts as a hit:
  - Targets are the basenames of non-test files in the patch, plus `def`/`class`/`function` names from the hunk headers.
  - A file hit is a basename appearing as a substring of the lowercased answer.
  - A function hit is a name of ≥ 5 characters appearing as a whole word. Function hits are recorded but do not affect risk.
- Risk levels:
  - `high`: every endpoint has a file hit.
  - `medium`: at least one endpoint has a file hit.
  - `low`: no file hits.
- An endpoint that errors has no file hit.

**Packaging that stage 4 relies on** (`harbor_packager.build_task`)
- `tests/test.sh` scores the run. The reward is the mean of the pass fractions for security, functional and (if `existing_expected.txt` is non-empty) existing tests.
  - The reward is 1.0 only if all of them are 1.0; otherwise it is at most 0.99 (`SCORE_PY`).
  - With no `ctrf.json`, scoring falls back to all-or-nothing on pytest's exit code.
- The first oracle and pre-patch runs have no `existing_expected.txt`. Existing tests run, but they do not affect the reward.
- Existing-test candidates (`select_existing_tests`, at most 15 files; `[]` for ecosystems other than PyPI/npm):
  - Test files the fix modified (score 100).
  - Files under `integration`, `e2e`, `playwright`, `selenium`, `cypress` or `benchmark` paths are excluded.
  - PyPI: test files that mention the changed module's dotted path, or its stem (≥ 5 characters) as a word.
  - npm: test files with a relative import of a changed module. If fewer than 3 files are found, all test files of the changed package(s) are added.
  - Pristine copies, plus parent `conftest.py`/`__init__.py` and the runner configs, go into `tests/existing_snapshot/`.

**Execution checks**

| Check (function) | Passes when | Otherwise |
|---|---|---|
| Oracle (`check_oracle`) | `--oracle-repeats` trials exist, all have a reward, and all rewards are exactly 1.0 | fewer trials or a missing reward: no verdict; reward < 1.0: terminal, with pytest feedback |
| Pre-patch (`check_pre_patch`) | reward < 1.0; both `test_security_*` and `test_functional_*` appear in `ctrf.json`; no security test passed; every functional test passed | no reward: no verdict; reward ≥ 1.0: terminal (no feedback); missing kind / a passing security test / a non-passing functional test: terminal, with feedback |
| Pass->pass (`derive_existing_expected`) | intersection of the existing tests that passed in every oracle trial and in the pre-patch trial; names with surrounding spaces or newlines are dropped | — |
| Oracle-final (`check_oracle` on `oracle-final`, only when the set is non-empty) | 1 trial with reward 1.0 | terminal without feedback, or no verdict |
| Require existing | set non-empty, or `--require-existing` off | terminal "out of spec" |
| Shallow patch (`check_fix_patches`) | ≥ 1 security test passed AND ≥ 1 security test did not pass | terminal, with `FIX-CHECK` feedback |
| Removal patch | ≥ 1 functional test did not pass, OR ≥ 1 test from `existing_expected.txt` did not pass | terminal, with `FIX-CHECK` feedback |
| Alternative patch | reward is 1.0 | terminal, with `FIX-CHECK` feedback + failing tests |
| Any check patch missing (`run_fix_checks`) | `check_patches/<kind>.patch` exists | terminal, with feedback |
| Any check run without reward or `ctrf.json` | — | no verdict |

Each check patch runs as the "oracle" of a hardlinked copy of `harbor_task` whose `solution/oracle_solution.patch` is replaced (k=1).

**Isolation audit** (`audit_task`). Every item must hold:
- `environment/` contains only `Dockerfile`, `repo`, `docker-compose.yaml`.
- Every `COPY`/`ADD` line is exactly `COPY repo/ /app/`.
- `repo/.git` exists, with `rev-list --all --count` = 1, no remote, no tags and ≤ 1 ref.
- Fix-leak blocks are taken from the oracle patch (test chunks included). A block is a run of added lines that are not also removed lines; blank lines do not break a run.
  - Source blocks must have ≥ 3 lines and ≥ 90 characters; test blocks ≥ 5 lines and ≥ 200 characters.
  - No block may appear in the whitespace-normalised repo tree (files < 2 MB) or in `instruction.md`.
- Network rules depend on the mode:
  - `proxy`: the main service is only on the internal `agent_isolated` network, with no own `network_mode`/`ports`. The egress `ALLOWED_HOSTS` is non-empty and a subset of the model-API hosts, the egress image is `cwe-egress:2`, and `task.toml` keeps Harbor's default (`public`) for both phases.
  - `no-network`: the compose file puts `main` on `network_mode: none`, and `task.toml` keeps the defaults.
  - Other modes: the agent `network_mode` equals the expected one and is not `public`. In `allowlist` mode the list must be non-empty with no non-model hosts, and the verifier is `no-network`.

**Image fix scan** (`fix_fingerprints`, `scan_image_for_fix`)
- Fingerprints are lines that are all of the following (at most 40):
  - added by the fix, in non-test files;
  - ≥ 40 characters after stripping, and containing 4 consecutive letters or underscores;
  - not an import or `require`/`export ... from` line, and not also removed in that file;
  - absent from every repo file under 3 MB.
- The scan builds the image (`docker build -q`, 1800 s) and runs `python3` inside with `--network none`.
  - It walks `/`, skipping `/proc`, `/sys`, `/dev`, `.git`, symlinks, files over 3 MB and binary files.
  - A file is a hit if it contains ≥ `min(2, len(fps))` fingerprints. At most 20 hits are reported.
- Results:
  - No fingerprints, or a failed image build, returns clean (the oracle run reports the build failure).
  - Scan errors or timeouts raise `ImageScanUnavailable`, which means no verdict.

**Outcomes and regeneration** (`process`, `archive_for_regeneration`)

| Verdict | Result |
|---|---|
| ok | `DONE`, eligible for stage 5 |
| terminal with feedback (oracle, pre-patch split, fix checks), round budget left | archived to `attempts/round_N`; stage 3 regenerates; no state change |
| `REJECTED_RUBRIC`, round budget left | archived (rubric issues travel in `rubric_check.json`) |
| terminal otherwise / budget used | state `FAILED_ORACLE` (default), `REJECTED_RUBRIC` or `REJECTED` (recall probe) |
| no verdict, detail matches a Docker-capacity marker | `state.reset` (requeued without a strike) |
| no verdict otherwise | `FAILED`; `FAILED_ORACLE` once attempts + 1 ≥ `MAX_NO_VERDICT` (2) |
| `QuotaExhausted` | stop the run, no state change; `HarborUnavailable` or crash: `FAILED` |

- The Docker-capacity markers are `fully subnetted`, `Docker compose command failed`, `Cannot connect to the Docker daemon` and `no space left on device`.
- `--max-regen` (default 2) caps the number of `round_*` directories. The budget is shared between rubric rejections and execution feedback.
- Archiving moves `instruction.md`, `hidden_tests.py`, `task_metadata.json`, `rubric_check.json`, `generation_meta.json` and `check_patches/`.

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `--skip-rubric`, `--skip-probe`, `--skip-fix-checks`, `--skip-image-scan` | off | Skip that step |
| `--probe-reject / --no-probe-reject` | on | Reject when the probe risk is `high` |
| `REQUIRE_EXISTING_TESTS` / `--require-existing` | `1` (on) | Reject tasks with an empty pass->pass set |
| `--oracle-repeats` | 2 | Oracle trials |
| `--timeout` | 3600 s | Minimum per `harbor run` |
| `--max-regen` | 2 | Regeneration rounds |
| `--model` / `ANTHROPIC_MODEL` | `claude-opus-5-5` | Rubric reviewer |
| `GEN_FALLBACK_MODEL` | `claude-opus-4-8` | Rubric retry model |
| `--workers` | 1 (pipeline: `min(--workers, 3)`) | Parallel tasks |
| `DEEPSEEK_*` / `MIMO_*` (`_API_KEY`, `_MODEL`, `_BASE_URL`, `_AGENT`) | see `Config.eval_endpoints` | Probe endpoints and network policy |
| `AGENT_NETWORK`, `TASK_CPUS`, `TASK_MEMORY_MB`, `AGENT_TIMEOUT_SEC`, `CLAUDE_CODE_VERSION`, `HARBOR_BIN` | derived from endpoints, 2, 3072, 3600, empty (installer default), venv or PATH | Packaging and Harbor |

`run_pipeline.py` passes only the skip/probe/require flags and `--only`/`--workers`. `--oracle-repeats`, `--timeout`, `--max-regen` and `--model` keep their defaults there.

## Code map

| File | Key functions |
|---|---|
| `src/stage4_oracle_validator/__init__.py` | `run`: maps pipeline flags to `oracle_runner` argv |
| `src/stage4_oracle_validator/oracle_runner.py` | `validate_task` (sequence); `check_oracle`; `check_pre_patch`; `derive_existing_expected`; `run_fix_checks` / `check_fix_patches`; `process` (routing); `archive_for_regeneration`; `pytest_feedback` |
| `src/stage4_oracle_validator/rubric_check.py` | `CRITERIA`; `check_task`; `evaluate_reply` |
| `src/stage4_oracle_validator/recall_probe.py` | `patch_targets`; `_ask`; `probe` |
| `src/stage6_packager/harbor_packager.py` | `build_task`; `select_existing_tests(_js)`; `split_patch_without_tests`; `audit_task`; `fix_fingerprints`; `scan_image_for_fix`; `TEST_SH` / `SCORE_PY` |
| `src/common/harbor.py` | `preflight`; `run_harbor`; `read_trials` / `read_trial` (reward, ctrf, exception) |
| `src/common/state_manager.py` | `should_process`, `mark` (FAILED increments attempts), `reset` |

## Known limitations

- **The "patch changed the code" check is not implemented.** The `oracle_runner` docstring says each check-patch outcome also proves that the patch changed the code ("differs from the pre-patch run"). `check_fix_patches` does not implement that comparison.
- **Pre-patch can pass without a per-test split.** If the pre-patch run produced no `ctrf.json`, `check_pre_patch` passes with only a warning, and the security/functional split is not verified.
- **Two terminal verdicts never trigger regeneration.** "Reward ≥ 1.0 on vulnerable code" and the `oracle-final` failure carry no feedback, so they go straight to terminal.
- **`--require-existing` cannot be turned off from the pipeline.** `run_pipeline.py --require-existing` can only add the flag, never remove it. Use `REQUIRE_EXISTING_TESTS=0` to turn it off.
- **The rubric is a filter, not a proof.** The reviewer is the same model family as the generator (module docstring). The "advisory" criterion type is supported but currently unused.
- **The recall probe ignores function hits.** Only file hits drive the risk, and a missing endpoint configuration silently skips the probe.
- **Some no-verdict cases never reach `FAILED_ORACLE`.** Exceptions (including a `harbor run` timeout) are marked `FAILED`. After 2 attempts `should_process` stops picking them, but they stay `FAILED` and never become `FAILED_ORACLE`.
- **Unclear: unapplicable check patch.** Stage 3 checks with `git apply --check`. If a check patch still fails to apply inside the image (`solve.sh` uses `set -e`), it is unclear how Harbor reports the trial. Stage 4 handles it only through the generic reward/ctrf checks.
- **Scan coverage gap.** The image scan treats a failed image build as clean. It relies on the oracle run to report the build failure.
