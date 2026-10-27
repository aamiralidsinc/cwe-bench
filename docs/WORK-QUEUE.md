# Work queue (phases 1 and 3, adoption)

Code: `common/queue/`. CLI: `python3 common/queue/cweq.py`. Settings: `common/queue/queue.toml`.
Tests: `python3 -m pytest common/queue/tests` (Python 3.11 or newer, for `tomllib`).

Phase 1 covers the work that follows a **test repair**: re-gate the task, then regrade or rescore every graded run.
It replaces hand-launched scripts such as `pipelines/router/out/queue/regate-regrade.sh`, `regrade-only.sh` and
`fastify-rescore.sh`. Builds, gates, trials, audits and fairness stay with the current scripts until phases 2 to 4.

## Design

1. **One job table.** A SQLite file (default `~/.tb-graders/cwe/queue.db`, WAL mode) with one row per job.
   A job is a kind, a task and its arguments. That triple is unique, so the same job can never be queued twice, and
   enqueuing an existing job changes nothing.
2. **A reconciler derives the jobs from the files.** It reads the artifacts that already hold the truth (the
   `build/<slug>/` markers and logs, the gate fingerprint, the repair folders and the trial folders). It never relies
   on what it planned before. The table holds only work in flight. If `queue.db` is deleted, the next
   `cweq reconcile` rebuilds the same jobs and skips work that is already finished on disk.
3. **A dispatcher starts jobs.** It is one process. It picks queued jobs by priority with aging: every hour a job
   waits raises its priority, so no job waits forever. It starts a job only within the limits in the settings file:
   a maximum number of running jobs per kind and in total, one job per task at a time, minimum free disk, maximum
   load, minimum available memory and a ceiling on `/tmp` inodes. Each job runs in a thin **worker**: its own
   session (setsid) that runs the existing script unchanged, refreshes a lease in the table, and records the exit code
   and the log path. A worker that dies, or whose lease expires, is stale. Its job goes back in the queue with one
   more attempt. Once the attempts are used up, the job is **blocked**, which means a person must look at it.
4. **A CLI, `cweq`**, covers these commands: `init`, `reconcile`, `dispatch`, `status`, `enqueue`, `retry`, `block`
   and `explain`. Every command that only looks, and every `--dry-run`, leaves the files unchanged.
5. **Tests** use a temporary database, a fake `build/` + `tasks/` + `jobs/` tree and fake worker commands
   (`true`, `false`, `sleep`). They cover:
   - idempotent enqueue;
   - priority and aging;
   - admission limits;
   - lease expiry, then requeue, then blocked;
   - dependencies;
   - rebuilding a deleted database without duplicates;
   - holds;
   - tasks that are busy with an old script.
6. **This document.**

## The rules (phase 1)

The reconciler looks only at tasks that have a test repair (`build/<slug>/repaired-tests-*/` or
`build/<slug>/removed-tests-*/`) or a hold (`build/<slug>/.hold-repair`).

| Files on disk | Job |
|---|---|
| A repair, the gate fingerprint is **stale** (`fingerprint.py check` would exit 1), and no gate `RESULT` line in `postbuild.log` is newer than the last change to the gated files | `regate` (`--listing` for `stk-` tasks, as in `router/regate_queue.py`) |
| A repair, the fingerprint is current, and `.gate_passed` is present with no re-gate running (it stopped between its gate and its `RESULT`) | `regate` |
| A repair, the fingerprint is current, and the last `RESULT` is `SOUND` | For each graded run whose grading (the original grading, or its newest `regrade-*`) is older than the newest change under `tasks/<slug>/tests/`: a `rescore` or a `regrade` (rules below) |
| The regate rule fires | The regrade and rescore jobs are queued at the same time, with `depends_on` set to the regate. They start when it is done. If it fails, they are blocked |
| `.hold-repair` (or `hold_<model>` for that model) | No `trial_run` of the task starts. Re-gates and regrades still run. After a re-gate of a held task, the worker moves `.sound` back to `.hold-repair`, as the repair scripts do. The hold is never released automatically |
| No fingerprint (gated before 2026-10-25) | No job. `explain` says so |
| A gate `RESULT` newer than the change that is not `SOUND` | No job. The re-gate failed on these files, so a person must look |
| An old script is working on the task | No job in this pass. Nothing starts for the task (see below) |

**Rescore or regrade.** A rescore (`rescore_from_results.py --drop`) is correct only when the repair removed tests
and changed nothing else. The reconciler uses a rescore when all of these hold:
- every file in `removed-tests-*` (without `.orig`, `.before` or `.relaxed`) is gone from `tasks/<slug>/tests/`;
- no `.orig` file in `repaired-tests-*` still has its file in the suite;
- each drop name hits the same test ids in the run's `results.json` as a whole word and as a substring.

The drop name is the file name up to its first dot (`invalid_schema_value.test.js` becomes `invalid_schema_value`).
In every other case, for example one function removed from a file that stays, it uses
`regrade_from_code.py <trial> "<why>"`. A run that has neither `final-code/changes.patch` nor `artifacts/` is
reported instead, and needs `regrade.py` run by hand.

**Already done.** A run needs nothing when it was graded or regraded after the tests last changed. For a rescore,
the run also needs nothing when one of its `regrade-*/REGRADE.json` files already lists every drop name in
`dropped`. That is how the queue avoids redoing work after `queue.db` is lost.

**Job keys** include `fp`, the first 16 hex digits of the gate digest of the current files. A repair queues its
jobs once per test version. A deleted database is rebuilt with the same keys. When the files change again, any
job still queued for the old version is marked `failed` with the result `superseded`. A queued job that the files
show done (because an old script did it) is marked `done` with the result `not needed any more`.

## Schema

`jobs` (one table; `common/queue/qdb.py`):

| Column | Meaning |
|---|---|
| `id` | integer key |
| `kind` | `build` `gate` `regate` `trial_run` `regrade` `rescore` `audit_prep` `fairness` `cleanup` |
| `task` | the slug |
| `args` | canonical JSON (sorted keys). `(kind, task, args)` is UNIQUE |
| `priority` | higher starts first. Effective priority = `priority + aging_per_hour × hours since queued_at` |
| `state` | `queued` → `leased` (claimed) → `running` (the worker started) → `done` / `failed`; `blocked` = needs a person |
| `attempts`, `max_attempts` | starts so far. A stale worker or a retryable exit code requeues the job until `attempts = max_attempts`, then blocks it |
| `owner_pid` | the worker wrapper. It leads its own session, so its process group id is the same number |
| `lease_expires` | UTC. The worker refreshes it every `lease_sec/10` |
| `depends_on` | JSON list of job ids that must be `done` first |
| `created`, `queued_at`, `started`, `finished` | UTC (`queued_at` is the last requeue; aging counts from it) |
| `exit_code`, `result`, `log_path` | the script's exit code, its last output line (or why the job was blocked), and its log |
| `origin` | `reconciler` or `manual`. The reconciler only supersedes its own jobs |

Exit codes: `0` → `done`. An exit code listed in `[retry_exit_codes]` → requeued, or blocked when the attempts are
used up. `regate.sh` exit 2 is a gate error caused by the infrastructure. Any other exit code → `failed` (not
retried; use `cweq retry <id>`).

## CLI

```
python3 common/queue/cweq.py init
python3 common/queue/cweq.py reconcile [--once] [--dry-run] [--task SLUG]
python3 common/queue/cweq.py dispatch  [--once] [--dry-run [--with-reconcile]] [-v]
python3 common/queue/cweq.py status
python3 common/queue/cweq.py enqueue KIND TASK [--args JSON] [--priority N] [--after ID]...
python3 common/queue/cweq.py retry ID          # also re-opens jobs blocked because this one failed
python3 common/queue/cweq.py block ID [--why TEXT]   # a running job's worker stops its script at the next refresh
python3 common/queue/cweq.py explain TASK      # what the rules see for the task, and all its jobs
```

Options before the command: `--db PATH` and `--config PATH` (or `$CWEQ_CONFIG`).
- `dispatch --dry-run` prints each job that would start, and for every other queued job the reason it waits:
  dependency, busy, held, at its limit, admission closed, or no worker for its kind.
- `dispatch --dry-run --with-reconcile` copies the queue into memory, reconciles into the copy, and then plans. It
  answers "what would the queue do right now?" and writes nothing.
- `status`, `explain` and the dry runs never create the database.

## Adoption: continuing from where the pipeline stands

The queue never starts from zero. Before the dispatcher starts anything, `cweq adopt` reads the state of every task
the pipeline knows into the database. The dispatcher stays closed (`require_adoption = true`) until an adoption has
been recorded with no conflicts.

- **What it reads** (`common/queue/taskstate.py`). It reuses the readers the current pipeline relies on: the
  scheduler's build-done rules, the gate markers and fingerprint, `trial_state.py`, the audited ledger,
  `fairness_verdict.py`, `HUMAN-DECISION.md`, and the delivery register `build/audit/delivered.tsv`. It also reads
  the processes running right now for builds, gates, re-gates, trials, fairness reviews and repairs.
- **Which tasks.** Every slug in a batch file, every ledger row, and every task package with a build record.
- **What it records.** Each task gets one stage and the one next step that moves it on. The stages are listed in
  `taskstate.STAGES`: from `waiting_build` through `trialing` and `awaiting_audit` to `kept` and `delivered`.
- **Running work.** Work that is running under the current scripts is recorded as running, never started a second
  time.
- **Older tasks.** A task from before the scale batches (not in a batch file, no `.sound` marker) is
  `outside_batches`. It is never built or gated. When the ledger has its verdicts, they decide its stage.
- **Delivery.** The delivery register is the record of what is in the client repository, so nothing is delivered
  twice. A delivery job appends a row to it.
- **Never redo.** Before a `build`, `gate` or `trial_run` job starts, and when one is enqueued by hand,
  `taskstate.redo_reason()` checks the files again. A job whose work the files show as done or running is closed as
  `done` ("not needed, it would redo finished work: ..."); it never runs. Holds are checked first, so a held task
  waits instead.
- **Conflicts.** A conflict is a reading that would make the queue repeat finished work or lose track of running
  work. Examples: a task package with no build record, a ledger verdict that the files do not explain, a running
  process for an unknown task. Conflicts keep the dispatcher closed.
- **Differences.** A difference is a place where the audited ledger and a model's runs log disagree, for example
  when runs of an older task version count in the ledger. Differences are shown for a person; the queue follows the
  ledger.

```
python3 common/queue/cweq.py adopt --dry-run [--detail]   # the report; writes nothing
python3 common/queue/cweq.py adopt                        # record it (tables adoptions, tasks)
python3 common/queue/cweq.py tasks [--stage S] [--next TEXT]
```

The per-batch schedulers are retired only after an adoption is OK and its counts match the schedulers' own state
files (builds running and waiting, trials running).

## Phase 3: builds and trials (replaces scale_queue.py)

Rules (`common/queue/phase3.py`, run in the same reconcile pass after the phase-1 rules). They cover only tasks
listed in a batch file, `pipelines/router/out/batches/*.txt`, or the batches named in `[phase3] batches`.

- **P1 build.** A task in stage `waiting_build` or `build_interrupted` that has `build/<slug>/BUILD-PROMPT.md` gets
  one `build` job, ever. A failed or declined build is final; `cweq retry` is a person's decision.
- **P2 trial_run.** A task in stage `waiting_trials` gets jobs for each model with no verdict. A model is skipped
  when it is stuck, or held by `hold_<model>`.
  - With no graded run yet, or one run left, the model gets one job with `--max-runs <left>`, which stops early at a
    solve.
  - After one failed run, each remaining run becomes its own one-run job, and they start together.
  - Job args carry `version`, the SOUND gate's fingerprint, so a new task version starts fresh keys, and queued jobs
    of the old version are superseded.
  - After `max_launches` launch groups end without a verdict, the model gets no more jobs and is reported for a
    person.
- **P3 regate.** A task in stage `stale_gate` gets `regate`, with the same key rule R1 uses.
- **Busy tasks.** A task that is building, re-gating, trialing or under repair gets nothing.
- **Never redo.** Nothing is planned or started that `taskstate.redo_reason()` refuses.

Workers run the scheduler's own commands:
- `build`: `run_stack_pipeline.sh <slug>` for `stk-` tasks, otherwise `run_pipeline.sh deepseek <slug>`.
- `trial_run`: `trial.py <slug> --models <m> --no-verdict --first-run N --max-runs K`, with
  `CWE_AGENT_TIMEOUT_MULT=1.5` from `[env.trial_run]`.
- Exit codes: `trial.py` exit 2 (some runs ungraded) counts as done, and the reconciler plans the next run. A build
  exits 0 on every recorded outcome. Exit 1 (STOP) and exit 3 (listing fail) show as failed, for a person.

Admission (`dispatch.py`), on top of the phase-1 limits:
- **Per-kind caps.** `[limits.max_running]`: build 20, trial_run 40.
- **Total cap.** `max_running_total` (69).
- **Old scripts count too.** Builds, trials and re-gates the old scripts are still running count against the per-kind
  and total caps (`count_foreign`), so old and new work together never exceed them.
- **Builds come first.** Trials wait while builds running plus builds queued reach `trials_wait_builds` (20), as
  `scale_queue.py --trial-threshold` did.
- **Disk floors per kind.** `[limits.disk_floor]` names a diskguard floor for build, trial_run and regate. The values
  live in `limits.env` and are read live.
- **Load and memory.** The same limits as phase 1.
- **Sharing a task.** A build, gate, regate, regrade or rescore runs alone on its task. The trial_runs of one task
  may run together, up to `max_running_per_task`.
- **Staggered starts.** `fill_spacing_sec` (15-40 s) during the first fill, then `start_spacing_sec` (2-8 s). This
  keeps simultaneous container start-up from starving sshd.

## Handover: draining the old schedulers (no cutover moment)

The old pipeline is drained, not switched off. Work it has already started finishes under it. Every next step is
started only by the queue: when a build the old scheduler started ends, the queue starts that task's gate and
trials. The queue counts the old work still in flight against its limits, so old and new together stay inside the
caps.

1. **Deploy** the queue code at `~/cwe-bench/common/queue`, and the `scale_queue.py` that knows the drain switch.
2. **Adopt.** `cweq adopt --dry-run`, then `cweq adopt`. The adoption must be OK, with zero conflicts.
3. **Check the plan.** `cweq dispatch --dry-run --with-reconcile` shows what would start and why the rest waits. Old
   running builds and trials appear as slots in use.
4. **Drain the schedulers.** `touch pipelines/router/out/queue/scale-b1.drain`, and the same for each running batch.
   - A scheduler that sees its drain file starts nothing more. It keeps polling and writing its state file, and
     exits when the last job it started has ended (its log says `drained`).
   - Its jobs run in their own sessions and never need the scheduler, so stopping a scheduler process outright is
     also safe. It only loses the state reporting.
   - A scheduler started before the drain switch existed must be restarted once with its same arguments to see the
     file. It never starts a second build of a running task (`build_alive`), and with the file present it starts
     nothing.
5. **Start the queue**, one of each:
   - `setsid nohup python3 common/queue/cweq.py reconcile ...`
   - `setsid nohup python3 common/queue/cweq.py dispatch ...`

   Use the same log locations as below.
6. **Verify.**
   - `cweq status`: the slots shown include the old work.
   - `cweq tasks --stage building` and `cweq tasks --stage trialing` should match the processes.
   - As old jobs end, their tasks' next steps appear as queue jobs.

**Rollback.**
1. Stop `cweq dispatch` and `cweq reconcile`. Queue workers that are running finish their current script.
2. Remove the `.drain` files. A scheduler that has not exited yet starts again.
3. Restart any scheduler that has exited, with its same arguments, for example
   `scale_queue.py run --batch pipelines/router/out/batches/scale-b3.txt --slots 20`. It adopts running work the same
   way, with `build_alive`, `trials_alive` and the trial state, so nothing runs twice.

## Running it alongside the current scripts

Phase 1 takes only jobs that the old scripts are not already doing.
- **Busy tasks.** Before it plans a task, and again before it starts a job, the queue reads the process table. A
  process whose command line matches one of the `[busy] patterns` (`regate`, `regrade`, `rescore`,
  `postbuild.sh`, `gate_one_ds.sh`, `gate.py`, `repair`, `upgrade`, ...) and names the task makes the task busy.
  The task can be named in the process's arguments or inside a small file the process was started with: the slug
  list of `regate_queue.py`, or a one-off script such as `fastify-rescore.sh`.
- **Busy is broad on purpose.** A `regate_queue.py` keeps every slug in its list busy until it exits, including
  slugs it has already finished. A `tail -f build/<slug>/regate.out` also counts.
- **Own workers.** Our workers and their children carry `CWEQ_JOB` in their environment and are never counted.
- **Same scripts.** The workers run the same scripts with the same arguments as the hand-run versions:
  `regate.sh <slug> [--listing]`, `regrade_from_code.py <trial> "<why>"` and
  `rescore_from_results.py <trial> --drop ... --why ...`. The VM-wide gate caps in `gate_one_ds.sh` still apply.
- **No double work.** A hand-started script and a queue job cannot run on the same task at once. Whichever finishes
  first leaves the files in a state that the reconciler reads as done.

Start (on the VM, from `~/cwe-bench`, one of each):

```
setsid nohup python3 common/queue/cweq.py reconcile >> ~/.tb-graders/cwe/queue-logs/reconcile.log 2>&1 < /dev/null &
setsid nohup python3 common/queue/cweq.py dispatch  >> ~/.tb-graders/cwe/queue-logs/dispatch.log  2>&1 < /dev/null &
```

## Switching it off

- **Stop new starts:** set `enabled = false` in `queue.toml`. The dispatcher still reaps stale workers but starts
  nothing (`status` shows `SWITCHED OFF`).
- **Stop everything:** kill the `cweq.py dispatch` and `cweq.py reconcile` processes. Running workers finish their
  current script and record it. A worker that you kill is reaped as stale by the next dispatcher.
- **One job:** `cweq block <id>`. The worker stops the script at its next lease refresh.
- **Remove it:** delete `queue.db`. Nothing else depends on it, and the old scripts keep working as before.

## Later phases

- **Phase 2: regrades chained into the rest.** After the last regrade of a task, queue the audit work. That means
  `audit_prep` for failing runs whose reward changed (the orchestrator's rule 5.4 step 4) and a ledger rebuild.
  Optionally release `.hold-repair` once every regrade is in, if the owner approves releasing automatically.
- **Phase 4: audits and fairness.** For each failing run without a current postmortem: `audit_prep`, then the audit.
  After 3 of 3 failures: `fairness` (the decision of 2026-10-19). `cleanup` jobs come from the janitor's approved
  reports.
