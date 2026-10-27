# common/: shared infrastructure

Everything here is used by **both** pipelines: `pipelines/sibling/` and `pipelines/stacking/`. There is one copy of
each file and one owner. Change a file here only when the change is right for both pipelines. A pipeline-specific
variant belongs in that pipeline's folder, as a wrapper that calls this file.

All locations are defined once, in **`paths.py`** (Python) and **`paths.sh`** (shell). Scripts import or source them
instead of building paths from their own location. The repo root is the folder holding `.cwe-bench-root`.

| Folder | Files | What they do |
|---|---|---|
| `launch/` | `drive.sh`, `run_build.sh`, `smoke.sh`, `models.env.example` | `drive.sh <deepseek\|mimo> <cmd…>` runs any agent step with Claude Code pointed at DeepSeek or MiMo; it sets `MODEL`, the endpoint, and token and timeout caps. `run_build.sh SLUG` runs the builder on `build/<slug>/BUILD-PROMPT.md`. `smoke.sh` is a one-line model check |
| `builder/` | `TASK-BUILD-PROMPT-v1.md`, `BUILDER.md`, `BRIEF-trap-stack.md`, `FRONTIER-CONFORMANCE-SPEC.md`, `PROMPT-TEMPLATES-SPEC.md`, `conformance_check.py`, `fmt_probe_gen.py`, `build_prepare.py`, `templates/` | The base build prompt and the rules a builder follows, the Frontier task format and its checker, the task skeleton, and `build_prepare.py`, which fills the prompt for one slug. Stacking appends its addendum to the same prompt |
| `screener/` | `SCREENER-PROMPT-v2.md`, `run_screener.py`, `records/` | The LLM host screener: prompt (with the `lessons-v2` block), runner (`--pick`, `--run`), and `records/`, the 150-host screened pool from 2026-10-17 |
| `gate/` | `gate.py`, `gate_one_ds.sh`, `docker-tuning.env` | Acceptance gate: static, nop (the pinned code fails every security test), oracle (the reference fix passes everything), patches (each check patch behaves as declared). `gate_one_ds.sh SLUG` runs nop, oracle and patches, retries infrastructure failures, and leaves exactly one of `.sound` / `.unsound` / `.gate_error`. `docker-tuning.env` is sourced by every Docker-touching script |
| `blindfix/` | `run_blindfix.sh`, `BLIND-FIX-BRIEF.md` | Blind fix: an independent agent fixes the task from the instruction alone. Its patch becomes a `kind: blind` check. It is a strict-gate prerequisite before shipping |
| `trial/` | `trial.py`, `run_trial.sh`, `trial_state.py`, `trial_set.sh`, `trial_summary.py`, `claude-code.Dockerfile.snippet`, `netguard/`, `netguard-check/`, `offline-check/`, `smoke-task/`, `harbor/` | `trial.py SLUG [--models m] [--first-run N --max-runs K] [--no-verdict]` runs early-abort trials through `run_trial.sh` (one harbor trial; honours `build/<slug>/hold_<model>`). `trial_state.py` gives launch decisions. `harbor/` holds the local harbor patches and how to re-apply them (**read `harbor/README.md` after any harbor reinstall**) |
| `audit/` | `postmortem.py`, `audit_results.py`, `review_flags.py`, `regrade.py`, `regrade_from_code.py`, `harvest_*.py`, `release_container.py`, `archive_runs.py`, `internet_use.py`, `own_repo.py`, `time_breakdown.py`, `gate_status.py`, `update_results.py`, `ledger_vm.py` | Post-run audit: `postmortem.py pending / prepare / record-ready`, with one Opus 5.5-high auditor per graded run. **`audit_results.py` is the only source of verdicts**; it writes `build/audit/ledger.md`. Regrade tools re-grade saved code; they can't grade separate-verifier tasks |
| `queue/` | `cweq.py`, `qdb.py`, `reconcile.py`, `dispatch.py`, `worker.py`, `procs.py`, `config.py`, `queue.toml`, `tests/` | The work queue (phase 1: re-gate, regrade, rescore after a test repair). One SQLite job table; a reconciler derives jobs from the files on disk; one dispatcher starts them within admission limits; workers run the existing scripts unchanged. See `docs/WORK-QUEUE.md` |
| `fairness/` | `FAIRNESS-REVIEW-BRIEF.md`, `fairness_verdict.py` | The fairness-review brief (two-gate split) and the verdict reader (READY / NOT_READY / ERROR). The launchers live in each pipeline |
| `versioning/` | `snapshot_experiment.sh`, `restore_snapshot.sh` | Before an in-place edit: snapshot the task version and its runs to `~/.tb-graders/cwe/experiments/<slug>/vN-<UTC>/` and bump `VERSION`. Undo a failed or no-op edit |
| `util/` | `agent_status.py`, `evidence.py`, `status_snapshot.sh`, `apply_docker_tweaks.sh`, `stop_lane.sh`, `rca_rerun.sh` + `rca/`, `stress_compose.sh`, `buildkit_test.sh` | Agent run status (ok or why not), full error evidence files, status snapshot, Docker daemon tuning, lane stop, root-cause re-runs, compose stress tests |
| `util/cutover_20261025.sh` | | One-time switch of the VM working tree to this layout (2026-10-25): idle check, rename the old tree to `~/cwe-bench-legacy-20261025`, clone, move `build/` and `tasks/`, merge run records, compare tool outputs before and after |
| `archive/` | | Old versions (`versions/`), superseded prompts, a stale template copy, old logs. See `archive/README.md` |

## Contracts other code relies on

- **Post-build checks** (2026-10-25): `common/gate/postbuild.sh <slug> [--listing]` runs the gate (static, then
  nop/oracle/patches in parallel), the blind fix and (stacking) the listing check at the same time, then the blind
  patch check; both pipelines' build chains call it.
- **Human decisions** (2026-10-25): `build/<slug>/HUMAN-DECISION.md` (`DECISION: KEEP|REPAIR|DROP`, `DATE:`) is the one
  place a person's answer to a fairness question goes; `fairness/fairness_verdict.py` reports it.
- **Gate fingerprint** (2026-10-25): `common/gate/fingerprint.py` records what a SOUND gate covered; trials and
  regrades refuse a task whose tests/solution/environment/checks changed since. See the re-gate rule in
  `pipelines/*/GUIDE.md`.
- **Blind fix tree** (2026-10-25): `common/blindfix/run_blindfix.sh` copies the image's working directory
  (`/workspace` or `/app`), not a fixed `/app`.
- **Delivery export** (2026-10-25): `common/util/export_delivery.py <out> <slug>...` writes the client layout
  `tasks/<task>/` + `trajectory/<task>/<model>/rollout<N>/{reward.json,trajectory.json,verifier/}`.

**Exit codes:**

| Script | Exit codes |
|---|---|
| `gate_one_ds.sh` | 0 sound, 1 unsound, 2 gate error |
| `trial.py` | 2 means incomplete |
| fairness and fairfix launchers | 0 finished, 1 not finished |

**Verdicts:**
- Read verdicts from `audit_results.py`, fairness results from `fairness_verdict.py`, and agent status from
  `agent_status.py`.
- **Never grep logs for verdicts.**

**VM host settings (outside the repo):**
- `/etc/docker/daemon.json`: address pools, `shutdown-timeout`, nofile.
- The docker/containerd systemd drop-ins: the grpc throttle fix, socket buffers, and `CPUWeight`.
- The harbor patches in `trial/harbor/`.

Run data lives outside the code: `build/<slug>/`, `tasks/<slug>/` and `~/.tb-graders/cwe/{jobs,experiments,work}`.
