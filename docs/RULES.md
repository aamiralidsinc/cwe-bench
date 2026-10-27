# Rule catalogue

Every automatic rule of the work queue (`common/queue/`). Each rule is written as **trigger** (what on disk makes
it fire), **action** (the job or decision), **outcome** (what the files show when the action succeeded) and
**check** (the code that verifies that outcome). Post-condition checks are in `common/queue/checks.py`; a job counts
as `done` only when its check passes (`checks.after_done`, called by `worker.py`); each kind's check is named in its
declaration (`common/queue/kinds/<kind>.py`). `cweq verify` runs the checks over finished jobs without changing them.

Check verdicts:
- **pass**: the outcome is on disk.
- **fail**: the job becomes `failed`, with the check named in its result.
- **person**: the job becomes `blocked`. A person looks: the step ran, but its result needs judgement.
- **none**: the kind has no file outcome; the exit code decides.

Every evaluation is a row in `job_checks`.

## Adoption and never-redo (`adopt.py`, `taskstate.py`)

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| A1 | `cweq adopt` | Read every known task (batch files, ledger rows, task packages with a build record) through `taskstate.read()` | One row per task in `tasks`, one row in `adoptions` with counts | `adopt.check()`: conflicts are listed and keep `ok = 0` |
| A2 | No adoption, or the newest has conflicts | The dispatcher starts nothing | `cweq status` and dry runs show the reason | `dispatch.plan()`: `require_adoption` |
| A3 | A `build`, `gate` or `trial_run` job is about to start or is enqueued by hand | `taskstate.redo_reason()` | A job whose work is done is closed as `done` ("not needed, it would redo finished work"). A job whose work is running waits | `test_adopt.py` never-redo tests |

## After a test repair (`reconcile.py`)

These rules apply to tasks with `build/<slug>/repaired-tests-*/`, `removed-tests-*/` or `.hold-repair`.

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| R1 | Repair present, gate fingerprint stale, no gate `RESULT` since the files last changed; or fingerprint current with `.gate_passed` and no re-gate running | `regate` (`--listing` for `stk-` tasks) | A `RESULT: SOUND` line at or after the job start, `.sound` (or `.hold-repair` for a held task), a fresh fingerprint matching the files | `checks.c_regate`: `regate.result`, `regate.marker`, `regate.fingerprint` |
| R2 | Repair present, fingerprint current, last `RESULT` SOUND, a graded run graded before the newest test change | `rescore` when the repair only removed whole test files and the names match exactly; otherwise `regrade`. Queued with `depends_on` the R1 regate when R1 fires | A new `regrade-<UTC>/` with `REGRADE.json` holding a numeric reward and `verifier/reward.json`. For a rescore, every dropped name is listed and absent from the new `results.json` | `checks.c_regrade`: `regrade.folder`, `regrade.scored` (person when the tool ran but could not score), `regrade.reward_file`, `rescore.method`, `rescore.dropped_listed`, `rescore.dropped_absent` |
| R3 | `.hold-repair` or `hold_<model>` | No `trial_run` of the task (or that model) starts | The job waits with the hold named | `dispatch.held()` |
| R4 | The repairs only removed tests and the ledger says both models solved | No job | Note "both models solved; removing tests cannot change the verdict" | `reconcile.removal_cannot_change_verdict()`, `test_reconcile.py` |
| R5 | Queued reconciler job whose key `fp` differs from the current files | Mark `failed`, result `superseded` | No old-version job starts | `reconcile.reconcile()` |

## Builds and trials (`phase3.py`)

These rules apply to tasks listed in a batch file.

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| P1 | Stage `waiting_build` or `build_interrupted`, `BUILD-PROMPT.md` present | One `build` job per task | `end_utc.txt` at or after the job start and not older than `start_utc.txt`. A recorded outcome: a gate marker written since the start, or a STOP / BUILD-INCOMPLETE / stopped line | `checks.c_build`: `build.ended`, `build.outcome` (person when the build ended without an outcome) |
| P2 | Stage `waiting_trials`, a model without a verdict, not stuck, not held | `trial_run` jobs: one early-abort job, or one job per remaining run after a failed run. Keys carry the task version | `runs_<model>.log` gains rows since the start for run `first_run`, and none outside `first_run .. first_run + max_runs - 1`. A held model needs no row | `checks.c_trial`: `trial_run.rows`, `trial_run.in_range` |
| P2b | `max_launches` launch groups of one (task, model, version) without a verdict | No more jobs; the model is reported for a person | Note in `cweq reconcile` output | `phase3.launches()` |
| P4 | A build ended with exit 124 more than 25 % after its time limit (`markers.build_paused`: the builder was paused and cut by its overdue timer on resume) | Stage `build_interrupted`; no `build` job; one `build_resume` job per interruption (key: the build's `end_utc`), sibling tasks only (stacking: reported for a person) | The builder session whose first task line names the slug is resumed (`resume_pipeline.sh`); `resume_start_utc.txt` and `end_utc.txt` after the job start, then a gate marker or a resumed-build log line | `kinds/build_resume.py` check: `build_resume.ran`, `build_resume.outcome` (person when there is no outcome) |
| M1 | A pipeline process (builder, gate, trial) stays stopped (SIGSTOP, state T) for `frozen_after_sec` | `monitor_alerts` row `process_frozen`; one urgent `process.frozen` event naming the tasks; preflight CRITICAL | The operator resumes or stops it; pausing is done by stopping new starts | `monitor.Monitor.add_frozen`, `preflight.check_frozen` |
| P3 | Stage `stale_gate` (R4 excepted) | `regate`, with the same key as R1 | As R1 | As R1 |

## Audits, fairness, cleanup and the router step (`phase4.py`)

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| F1 | A run in `build/audit/awaiting_audit.tsv` with no postmortem folder for its current grading. Skipped when the task is rejected with both models solved, held or busy with a repair, or when the run's model already solved the task | `audit_prep` | `<trial>/postmortem-<UTC>/PREPARED.json` at or after the start | `checks.c_audit_prep`: `audit_prep.prepared` |
| F2 | Every pass | Rewrite `pipelines/router/out/queue/audit_ready.txt` with the prepared folders waiting for an auditor | The file lists exactly those folders | `phase4.write_ready()` |
| F3 | An auditor's `verdict.json` not recorded yet, or a trial result or regrade newer than the ledger | `audit_record` (`postmortem.py record-ready`, then `audit_results.py`) | `build/audit/ledger.md` and `trials.tsv` rewritten at or after the start | `checks.c_audit_record` |
| F4 | A batch task the ledger marks BREAKER candidate, no `FAIRNESS.md` newer than its newest trial job folder, no review running, not held or busy | `fairness` (stacking or sibling review) | `FAIRNESS.md` written at or after the start, `fairness_status.txt` says ok, and a verdict READY or NOT_READY | `checks.c_fairness`: `fairness.review`, `fairness.finished`, `fairness.verdict` (person when the review states no verdict) |
| F5 | Every UTC hour, no other cleanup loop running | `cleanup` (`hourly_cleanup.sh once`) | A `pass done` line in `build/audit/hourly_cleanup.log` at or after the start | `checks.c_cleanup` |
| F6 | Every UTC half hour | `step3`: `route.py step3` routes newly solved stacked tasks into the general sibling pool, then `route.py pool` when something new was routed | Solved stacked tasks are ranked with every other sibling candidate; nothing is prepared or selected | none (the exit code decides) |
| L1 | A batch task SOUND on its gate (stage waiting_trials or later) with no `build/<slug>/lint/<fp>.json` for its current gate fingerprint (`lintstep.py`) | `lint` (`lintstep.py run`: `common/lint/task_lint.py`, warning-only) | `build/<slug>/lint/<fp>.json` with warning and note counts, written at or after the start | `checks.c_lint`: `lint.result` |

## Admission (`dispatch.py`)

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| D1 | A queued job | Start in order of priority + `aging_per_hour` × hours waited | No job waits forever | `test_queue.py` aging test |
| D2 | A kind at `[limits.max_running]`, or all kinds at `max_running_total`; work started outside the queue counts | The job waits | Running jobs never exceed the caps | `dispatch.plan()`, `test_phase3.py` |
| D7 | CPU idle stayed >= `[autolimit] raise_idle_pct` for `raise_window_min` with work queued, or <= `lower_idle_pct` for `lower_window_min` | `max_running_total` moves one `step`, between the base and `ceiling`, at most once per `cooldown_min` | The limit follows sustained load, never one reading; lowering stops nothing | `autolimit.step()`, `test_batch_order_autolimit.py` |
| D8 | A batch file says `# hold: yes`, or a reconciler-queued build's task left every batch file | The build waits | A held or re-ranked batch starts no new builds; lifting the hold resumes them | `dispatch.batch_hold()`, `test_batch_order_autolimit.py` |
| P3-order | Batch tasks are planned | In batch-file order; `# priority: <int>` adds to the batch's build and trial priorities | Earlier batches and higher-ranked lines start first | `phase3.reconcile()`, `test_batch_order_autolimit.py` |
| D3 | Free disk under the kind's diskguard floor; load, memory or `/tmp` inodes over their limits | The job waits (bookkeeping kinds are exempt) | Nothing heavy starts on a short machine | `dispatch.plan()` |
| D4 | A build, gate, regate, regrade or rescore of the task is running | Other jobs of the task wait | One exclusive job per task | `dispatch.plan()` |
| D5 | The newest real `cweq selfcheck --run` of `regrade` or `rescore` failed (`[checks] refuse_on_failed_selfcheck`) | Jobs of that tool wait | No grading runs with a tool that does not reproduce a known result | `checks.tool_refused()`, `test_checks.py` |
| D6 | A worker dies or its lease expires | Requeue with one more attempt, or block when attempts are used up | No job is lost or left running twice | `dispatch.reap()` |

## Kinds and settings (`kinds/`, `settings.py`)

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| K1 | A job of a kind is queued or started | `enqueue()` refuses a kind no declaration registers; the worker runs the declaration's command | Only declared kinds run | `qdb.enqueue()`, `test_kinds.py` |
| K2 | A declaration has `plan` | Its plan runs at the end of each reconcile pass and queues its jobs (idempotent keys) | A plug-in stage is planned like the built-in ones | `reconcile.reconcile()`, `test_kinds.py` |
| K3 | A loop starts, or the settings file's hash differs from the version in force | Record the version in `settings`; continue with the new values | Every version in force is in the history | `settings.refresh()`, `test_kinds.py` |
| K4 | A worker starts a job | The job records the settings version the worker loaded | `cweq explain` shows the version a job ran under | `qdb.start()`, `test_kinds.py` |

## Self-checking tools (`checks.py`, `cweq selfcheck`)

| Tool | Reference run | Reproduction | Pass |
|---|---|---|---|
| `regrade_from_code.py` | The newest original grading with saved code, a reward strictly between 0 and 1, and tests unchanged since it was graded | The tool runs on a private copy of the run folder (`[checks] selfcheck_dir`); the real run folder is never written | The same reward |
| `rescore_from_results.py` | The newest run whose newest regrade is a rescore, with tests unchanged since | The same drops replayed on a private copy | The same reward |

`cweq selfcheck` without `--run` records and prints the reference it would use; `--run` costs one grading for
`regrade` and none for `rescore`. Results are rows in `selfchecks`.
