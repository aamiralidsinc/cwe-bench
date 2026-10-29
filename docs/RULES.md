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
| R2 | Repair present, fingerprint current, last `RESULT` SOUND, a graded run whose grading in use was not made on the current tests, judged by content (2026-10-28): the grading's test version (`REGRADE.json` `tests_hash` or its verifier image tag; the original grading: the `cwe-reuse/<task>:verifier-<hash>` image in the run's `trial.log`) differs from the content hash of `tasks/<slug>/tests/`. A regrade that did not score is not a grading. A grading with no recorded version: `[reconcile] unknown_tests_version` (`regrade` once, `repair_folder`, or `mtime`, the older rule) | `rescore` when the repair only removed whole test files and the names match exactly; otherwise `regrade`. Queued with `depends_on` the R1 regate when R1 fires | A new `regrade-<UTC>/` with `REGRADE.json` holding a numeric reward, `tests_hash` and `verifier/reward.json`. For a rescore, every dropped name is listed and absent from the new `results.json` | `checks.c_regrade`: `regrade.folder`, `regrade.scored` (person when the tool ran but could not score), `regrade.reward_file`, `regrade.tests_current`, `rescore.method`, `rescore.dropped_listed`, `rescore.dropped_absent` |
| R3 | `.hold-repair` or `hold_<model>` | No `trial_run` of the task (or that model) starts | The job waits with the hold named | `dispatch.held()` |
| R4 | The repairs only removed tests and the ledger says both models solved | No job | Note "both models solved; removing tests cannot change the verdict" | `reconcile.removal_cannot_change_verdict()`, `test_reconcile.py` |
| R5 | Queued reconciler job whose key `fp` differs from the current files | Mark `failed`, result `superseded` | No old-version job starts | `reconcile.reconcile()` |
| R6 | `.hold-repair`, a repair, fingerprint current, last `RESULT` SOUND, every graded run graded on the current tests (R2 wants nothing, no run without saved code), no regate / regrade / rescore / repair job of the task queued or running, none failed or blocked for this version, the hold not newer than that `RESULT` and not saying `repair failed` (`[repair] lift_holds`) | The queue lifts the hold: `.hold-repair` -> `.sound` | `.sound` present, `.hold-repair` gone, the fingerprint still current; a line in `build/<slug>/repair-<date>.log` | `reconcile.lift_hold()` (post-condition; event `repair.hold_lift_failed` when it fails), `test_repair.py` |
| R7 | A repair job of the task is leased or running | The task is not analysed this pass | Nothing is planned on files the agent is editing | `reconcile.reconcile()` |

## Test repairs (`repairstep.py`, `repairjob.py`, `kinds/repair.py`)

The repair step was the fairfix step (`pipelines/sibling/10-fairfix/run_fairfix.sh`, `pipelines/stacking/8-fairfix/run_fairfix_stack.sh`), started by an Opus orchestrator and run on DeepSeek; it was lost in the move to the work queue (no job kind) and is a queue job again since 2026-10-28 (history: `docs/WORK-QUEUE.md`).

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| T1 | An uncovered finding: (a) a recorded post-run audit on the grading in use names failing tests unfair (`test-fault`, `instruction-ambiguity`, an `unfair_kind`) and they decided a run (run attribution test-fault / instruction-ambiguity, or the run fails no fair test), or the task is kept or delivered (standing rule: fix every unfair test); (b) `FAIRNESS.md` NOT_READY with test-only required changes, or a deciding CONFLICTS line without a CONFLICTS-RULED KEEP; (c) a current `DECISION: REPAIR`. Not when: dropped or withdrawn; a repaired-tests-* / removed-tests-* / testfix-* folder is newer than the finding; a repair already ran for the same finding (`repair-inputs-*/FINDING.json`); another repair of the task is queued or running; the task is held; `max_per_task` repairs ran; `skip_solved` and a model solved a task that is not kept | `[repair] auto = true`: one `repair` job, key `{"finding": <key>}` (a queued job for an older finding is superseded). `auto = false` (first deploy): no job; the plan is shown by `cweq explain`, `cweq repairs` and the inbox, event `repair.planned` | A job with the finding's key | `repairstep.plan()`, `test_repair.py` |
| T2 | A `repair` job starts | The job sets `.hold-repair`, waits for the task's other work (`wait_sec`, else the hold goes back and exit 75 blocks the job for a person; `max_attempts` 1, never restarted on its own), writes `repair-inputs-<UTC>/` (finding, every graded run's per-test failures, final diff, transcript excerpts), backs up the task, runs the fairfix script in repair mode on DeepSeek, checks the result in code | Exit 0: a new repair folder with README, `history/<date>-repair.md`, instruction.md / task.toml / environment unchanged, the static gate stage still passing, changed test files touched, the hold kept, a `regate` queued with the R1 key (also for a task with no fingerprint). Otherwise the originals are restored, the agent's folder moved to `failed/`, the hold keeps the reason (exit 1; exit 3 for no repair) | `kinds/repair.py` check: `repair.result`, `repair.folder`, `repair.instruction_kept` (person), `repair.held` |
| T3 | Every pass | `cweq repairs --lost` and one inbox line: tasks with a test-fault audit and no later repaired-tests-* / removed-tests-* / testfix-* folder | The list (dropped and withdrawn tasks marked) | `repairstep.lost()`, `test_repair.py` |

## Builds and trials (`phase3.py`)

These rules apply to tasks listed in a batch file.

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| P1 | Stage `waiting_build` or `build_interrupted`, `BUILD-PROMPT.md` present | One `build` job per task | `end_utc.txt` at or after the job start and not older than `start_utc.txt`. A recorded outcome: a gate marker written since the start, or a STOP / BUILD-INCOMPLETE / stopped line | `checks.c_build`: `build.ended`, `build.outcome` (person when the build ended without an outcome) |
| P2 | Stage `waiting_trials`, a model without a verdict, not stuck, not held | `trial_run` jobs: one early-abort job, or one job per remaining run after a failed run. Keys carry the task version | `runs_<model>.log` gains rows since the start for run `first_run`, and none outside `first_run .. first_run + max_runs - 1`. A held model needs no row | `checks.c_trial`: `trial_run.rows`, `trial_run.in_range` |
| P2b | `max_launches` launch groups of one (task, model, version) without a verdict | No more jobs; the model is reported for a person | Note in `cweq reconcile` output | `phase3.launches()` |
| P2c | A graded run the ledger leaves out for an UNTRUSTED post-run audit (its cell says `audit: untrusted`) whose cause is not a test fault the repair step owns (`untrusted.py` action `rerun`: harness or infrastructure, provider stop, rate limit, partial workspace; or a test fault nobody repairs, or a repaired one whose regrade was audited again and is still untrusted) | The run no longer counts as graded for the launch rules (`trial_state` `drop=`): the stage is `waiting_trials` and P2 plans a fresh run. A `stuck` model gets exactly one fresh run per untrusted run (args `rerun_of`). Holds, `hold_<model>` (blocked models) and P2b apply | As P2 | `taskstate.read()`, `phase3.rerun_plan()`, `test_untrusted.py` |
| P4 | A build ended with exit 124 more than 25 % after its time limit (`markers.build_paused`: the builder was paused and cut by its overdue timer on resume); or, with `[build_resume] auto_timeouts = true`, a genuine 5-hour timeout (stage `build_stopped`, at most `max_auto_resumes` per task) | Stage `build_interrupted` (paused) or `build_stopped` (timeout); no `build` job; one `build_resume` job per interruption (key: the build's `end_utc`; a job queued by hand for that end counts), sibling tasks only (stacking, `STOP.md`, kills: reported for a person) | The builder session whose first task line names the slug is resumed (`resume_pipeline.sh`); `resume_start_utc.txt` and `end_utc.txt` after the job start, then a gate marker or a resumed-build log line | `kinds/build_resume.py` check: `build_resume.ran`, `build_resume.outcome` (person when there is no outcome) |
| M1 | A pipeline process (builder, gate, trial) stays stopped (SIGSTOP, state T) for `frozen_after_sec` | `monitor_alerts` row `process_frozen`; one urgent `process.frozen` event naming the tasks; preflight CRITICAL | The operator resumes or stops it; pausing is done by stopping new starts | `monitor.Monitor.add_frozen`, `preflight.check_frozen` |
| P3 | Stage `stale_gate` (R4 excepted) | `regate`, with the same key as R1 | As R1 | As R1 |

## Audits, fairness, cleanup and the router step (`phase4.py`)

| # | Trigger | Action | Outcome | Check |
|---|---|---|---|---|
| F1 | A run in `build/audit/awaiting_audit.tsv` with no postmortem folder for its current grading. Skipped when the task is rejected with both models solved, held or busy with a repair, or when the run's model already solved the task, or when the run's current grading (newest regrade) is a solve | `audit_prep` | `<trial>/postmortem-<UTC>/PREPARED.json` at or after the start | `checks.c_audit_prep`: `audit_prep.prepared` |
| F1b | An untrusted test-fault / instruction-ambiguity audit covered by a newer repair folder, whose grading in use (the R2 regrade) is on the current tests while the audit is carried over from an older grading (`untrusted.py` action `reaudit`). Same skips as F1. Covered but not regraded yet: `wait_regrade`; a test fault the repair step owns (`.hold-repair`, a repair job queued or running, T1 plans one): `wait_repair`. None of them is re-run | `audit_prep` of the regrade | As F1 | `phase4.reaudits()`, `test_untrusted.py` |
| F2 | Every pass | Rewrite `pipelines/router/out/queue/audit_ready.txt` with the prepared folders waiting for an auditor | The file lists exactly those folders | `phase4.write_ready()` |
| F3 | An auditor's `verdict.json` not recorded yet, or a trial result or regrade newer than the ledger | `audit_record` (`postmortem.py record-ready`, then `audit_results.py`) | `build/audit/ledger.md` and `trials.tsv` rewritten at or after the start | `checks.c_audit_record` |
| F4 | A batch task the ledger marks BREAKER candidate, no review running, not held or busy, and no current review: `FAIRNESS.md` newer than its newest trial job folder AND made on the current tests (`fairness_tests.json` holds the tests hash the review was shown; without it, no repaired-tests-* / removed-tests-* / testfix-* folder newer than the last review). Key `{"after": <trial job folder>, "tests": <tests hash>}`; an older `{"after"}` job still stands for unchanged tests (`phase4.py` F1) | `fairness` (stacking or sibling review); a stale review is moved to `FAIRNESS.md.prev-<UTC>` when its job is queued | `FAIRNESS.md` written at or after the start, `fairness_status.txt` says ok, and a verdict READY or NOT_READY | `checks.c_fairness`: `fairness.review`, `fairness.finished`, `fairness.verdict` (person when the review states no verdict) |
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
| D9 | A `repair` job whose task has other work queued or running (queue jobs other than bookkeeping, a queued `trial_run` that the hold does not stop, old-script processes) | The repair waits | A repair never edits the tests under a running trial, re-gate or regrade | `dispatch.repair_waits()`, `test_repair.py` |
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
