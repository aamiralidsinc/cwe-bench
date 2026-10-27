# Work queue

Code: `common/queue/`. CLI: `python3 common/queue/cweq.py`. Settings: `common/queue/queue.toml`.
Tests: `python3 -m pytest common/queue/tests` (Python 3.11 or newer, for `tomllib`).

One queue starts every stage of the pipeline:
- builds and gates;
- trials;
- the re-gate, regrade and rescore that follow a test repair;
- audit preparation and recording;
- fairness reviews;
- the hourly cleanup;
- the router's periodic step;
- delivery preparation after the owner's keep decision.

It also keeps an event queue for the orchestrator and a decisions inbox for the owner. Together these implement
section 1 of `docs/ARCHITECTURE-ROADMAP.md`, plus the event queue and decisions inbox of section 4 and the delivery
job of section 8.

## Design

1. **One job table.** The table is a SQLite file (default `~/.tb-graders/cwe/queue.db`, WAL mode) with one row per
   job. A job is a kind, a task and its arguments. That triple is unique, so the same job can never be queued twice,
   and enqueuing an existing job changes nothing.
2. **A reconciler derives the jobs from the files.** It reads the artifacts that already hold the truth:
   - the `build/<slug>/` markers and logs;
   - the gate fingerprint;
   - the repair folders and trial folders;
   - the audited ledger;
   - fairness reviews and keep decisions.

   It never relies on what it planned before. The table holds only work in flight. If `queue.db` is deleted, the next
   pass rebuilds the same jobs and skips work that is already finished on disk.
3. **A dispatcher starts jobs.** It is one process. It picks queued jobs by priority with aging: every hour a job
   waits raises its priority, so no job waits forever. It starts a job only within the limits in the settings file
   (see Admission).

   Each job runs in a thin **worker**. The worker runs in its own session (setsid). It runs the stage's existing
   script unchanged, refreshes a lease in the table, and records the exit code and the log path.

   A worker that dies, or whose lease expires, is stale. Its job goes back in the queue with one more attempt. Once
   the attempts are used up, the job is **blocked**, which means a person must look at it.
4. **A shared task-state reader** (`common/queue/taskstate.py`) gives every task one stage and the one next step that
   moves it on. It reuses the readers the pipeline already relies on:
   - the build-done rules;
   - the gate markers and fingerprint;
   - `trial_state.py`;
   - the audited ledger;
   - `fairness_verdict.py`;
   - `HUMAN-DECISION.md`;
   - the delivery register `build/audit/delivered.tsv`.

   It also reads the processes running for each task.
5. **A CLI, `cweq`.** Every command that only looks, and every `--dry-run`, leaves the files unchanged.
6. **Tests.** They use a temporary database, a fake `build/` + `tasks/` + `jobs/` tree and fake worker commands
   (`true`, `false`, `sleep`). They cover:
   - idempotent enqueue, priority and aging;
   - admission limits;
   - lease expiry, then requeue, then blocked;
   - dependencies, and rebuilding a deleted database without duplicates;
   - holds and busy tasks;
   - adoption and the never-redo rule;
   - every build, trial, audit, fairness and cleanup rule.

## Adoption: continuing from where the pipeline stands

The queue never starts from zero. Before the dispatcher starts anything, `cweq adopt` reads the state of every task
the pipeline knows into the database. The dispatcher stays closed (`require_adoption = true`) until an adoption has
been recorded with no conflicts.

- **Which tasks.** Every slug in a batch file, every ledger row, and every task package with a build record.
- **What it records.** Each task gets a stage, from `waiting_build` through `trialing` and `awaiting_audit` to `kept`
  and `delivered` (the full list is `taskstate.STAGES`), plus its next step.
- **Running work.** Work that is already running is recorded as running and never started a second time.
- **Older tasks.** A task outside the batch files that has no `.sound` marker is `outside_batches`. It is never built
  or gated. When the ledger has its verdicts, they decide its stage.
- **Never redo.** `taskstate.redo_reason()` checks the files again before a `build`, `gate` or `trial_run` job
  starts, and whenever one is enqueued by hand. If the files show the work done or running, the job is closed as
  `done` and never runs. Holds are checked first, so a held task waits instead.
- **Conflicts.** A conflict is a reading that would make the queue repeat finished work or lose track of running work.
  Examples: a task package with no build record, a ledger verdict that the files do not explain, a running process
  for an unknown task. Conflicts keep the dispatcher closed.
- **Differences.** A difference is a place where the audited ledger and a model's runs log disagree, for example when
  runs of an earlier task version count in the ledger. Differences are shown for a person; the queue follows the
  ledger.

```
python3 common/queue/cweq.py adopt --dry-run [--detail]   # the report; writes nothing
python3 common/queue/cweq.py adopt                        # record it (tables adoptions, tasks)
python3 common/queue/cweq.py tasks [--stage S] [--next TEXT]
```

## Rules

The reconciler runs every `tick_sec` (120 s). Each pass applies three groups of rules in order.

### After a test repair (`common/queue/reconcile.py`)

These rules apply to tasks that have a test repair (`build/<slug>/repaired-tests-*/` or `removed-tests-*/`) or a hold
(`build/<slug>/.hold-repair`).

| Files on disk | Job |
|---|---|
| A repair, the gate fingerprint is **stale**, and no gate `RESULT` is newer than the last change to the gated files | `regate` (`--listing` for `stk-` tasks) |
| A repair, the fingerprint is current, and `.gate_passed` is present with no re-gate running | `regate` |
| A repair, the fingerprint is current, and the last `RESULT` is `SOUND` | For each graded run whose grading (the original or its newest `regrade-*`) is older than the newest change under `tasks/<slug>/tests/`: a `rescore` or a `regrade` |
| The regate rule fires | The regrade and rescore jobs are queued at the same time, with `depends_on` set to the regate |
| The repair only removed tests, and both models already solved the task | No job: removing tests cannot change that verdict |
| `.hold-repair` (or `hold_<model>`) | No `trial_run` of the task starts. Re-gates and regrades still run |
| A gate `RESULT` newer than the change that is not `SOUND` | No job: a person looks |

- **Rescore or regrade.** A rescore (`rescore_from_results.py --drop`) is used only when the repair removed whole
  test files and changed nothing else, and each dropped name hits the same test ids as a whole word and as a
  substring. In every other case the queue uses `regrade_from_code.py`.
- **Job keys.** They include `fp`, the first 16 hex digits of the gate digest, so a repair queues its jobs once per
  test version. When the files change again, jobs still queued for the old version are superseded.

### Builds and trials (`common/queue/phase3.py`)

These rules apply to tasks listed in a batch file (`pipelines/router/out/batches/*.txt`).

- **Build.** A task waiting for its build, or whose build was interrupted, gets one `build` job, provided
  `build/<slug>/BUILD-PROMPT.md` exists. A failed or declined build is final; `cweq retry` is a person's decision.
- **Trials.** A task waiting for trials gets `trial_run` jobs for each model that has no verdict yet. Models that are
  stuck or held by `hold_<model>` get none.
  - With no graded run yet, or with one run left, the model gets one job that stops early at a solve.
  - After one failed run, each remaining run becomes its own one-run job, and they start together.
  - Job arguments carry the task version (the SOUND gate's fingerprint), so a new version starts fresh.
  - After `max_launches` launch groups end without a verdict, the model is reported for a person.
- **Stale gate.** A sound task whose files changed since its gate gets a `regate`.
- Workers run the pipeline's own commands:
  - build: `run_stack_pipeline.sh` or `run_pipeline.sh`;
  - trial: `trial.py --no-verdict --first-run N --max-runs K`, with the agent time-limit multiplier from
    `[env.trial_run]`.

### Audits, fairness, cleanup and the router step (`common/queue/phase4.py`)

| Kind | When | Command |
|---|---|---|
| `audit_prep` | A failing run waits for its audit. Not for a task held or busy with a repair (its grading is about to change), and not when the run's model already solved the task. A folder prepared before a regrade is replaced | `postmortem.py prepare <trial>` |
| `audit_record` | An auditor's `verdict.json` is not recorded yet, or a trial result is newer than the ledger | `postmortem.py record-ready`, then `audit_results.py` |
| `fairness` | The ledger marks a batch task a BREAKER candidate, and no review is current or running. Never while held or busy | the stacking or sibling fairness review |
| `cleanup` | Every UTC hour | `common/util/hourly_cleanup.sh once` |
| `step3` | Every UTC half hour | the router's periodic step |

- **Audit list.** Every pass rewrites `pipelines/router/out/queue/audit_ready.txt` with the prepared folders waiting
  for an auditor. The audit itself is an independent reviewer's job; the queue prepares and records.
- **Pseudo tasks.** `audit_record`, `cleanup` and `step3` run as the pseudo tasks `_ledger`, `_machine` and
  `_router`.

### Delivery preparation (`common/queue/delivery.py`)

A task gets one `delivery_prep` job per keep decision when all of these hold:
- its `HUMAN-DECISION.md` records a current KEEP;
- the audited ledger shows both models failed;
- it is not in the delivery register (`build/audit/delivered.tsv`).

A kept task that is not a both-model breaker is reported and never prepared.

The job runs `delivery.py prep <slug>`:
1. `common/util/export_delivery.py` writes the task package and its counted rollouts into
   `~/.tb-graders/cwe/deliveries/<UTC>-<slug>/` (`[delivery] out_dir`). The export redacts every model key value.
2. `task.toml` gets `name = "cwe-bench/<name>"`; nothing else in the package changes.
3. A pattern scan of the whole export must find no key-like strings outside upstream test fixtures.
4. `ready.json` records the result:
   - the proposed name (the repository name plus the CWE's short name, in kebab case);
   - the README row;
   - rollouts per model, and runs skipped for lack of a trajectory;
   - both scan results.

The job never touches the delivery repository; the commit and push are done by a person. After the push,
`cweq delivered <slug> <name> <commit>` appends the register row (and the `-control` row of a stacked task) and the
`DELIVERED` line in `HUMAN-DECISION.md`.

## Events

Each reconcile pass turns what changed into rows of the `events` table (`common/queue/events.py`):

| Event | When |
|---|---|
| `job.done`, `job.failed`, `job.blocked` | A job ended. `done` is emitted only for the kinds in `[events] job_done_kinds` |
| `stage.<stage>` | A task reached a new stage, for the stages in `[events] stages` |
| `breaker.candidate` | The audited ledger now calls the task a BREAKER candidate |
| `audit.ready` | An evidence folder waits for its auditor |
| `adoption.conflict` | The latest adoption has a conflict |
| `disk.critical` | Free disk fell below `[events] disk_critical_gb` |

- **No duplicates.** Every event has a dedup key, and the values an event compares against (a task's stage, its
  ledger verdict, the disk state) are kept in the `marks` table. The same change therefore never emits twice.
- **Quiet first pass.** The first pass records the marks without emitting, so history does not flood the table.
- **Handling order.** `cweq events next` returns the oldest open event, urgent kinds first (`[events] urgent`).
  `cweq events handle ID --action TEXT` closes an event with the action taken. Events are handled one at a time,
  in that order.

## Decisions inbox

`cweq inbox` prints, and `cweq inbox --html PATH` writes as one self-contained page, every decision waiting on the
owner. Everything comes from `taskstate`, `fairness_verdict`, `HUMAN-DECISION.md`, the job table and the prepared
delivery packages. The sections are:
- breakers ready for KEEP, REPAIR or DROP, with the reviewer's human-review question quoted from `FAIRNESS.md`;
- fairness reviews that are NOT READY, with the required change quoted;
- kept tasks that are not delivered yet, with their prepared package;
- blocked jobs;
- tasks that need a person (listing check failed, trials stuck).

## Admission

No job starts while any limit is exceeded:

| Limit | Value |
|---|---|
| Running per kind (`[limits.max_running]`) | build 32, trial_run 40, regate 15, regrade 3, rescore 2, fairness 3, cleanup 1, delivery_prep 1 |
| Running in total (`max_running_total`) | 69 |
| Free disk | a floor per kind (`[limits.disk_floor]`), read live from `limits.env` through `common/util/diskguard.py` |
| Machine | maximum load, minimum available memory, ceiling on `/tmp` inodes (from the monitor's latest sample while it is under 2 minutes old, otherwise measured) |
| Per task | one build, gate, re-gate, regrade or rescore at a time; a task's trial runs may run together |

Further rules:
- **Work started outside the queue counts too.** Builds, trials, re-gates and fairness reviews started by other
  launchers count against the per-kind and total caps.
- **Bookkeeping kinds.** `audit_prep`, `audit_record`, `cleanup` and `step3` sit outside the total and machine limits,
  so the cleanup still runs when disk is short. Each keeps its own cap.
- **Staggered starts.** Starts are spaced 15-40 s apart during the first fill, then 2-8 s, so simultaneous container
  start-up never starves the machine.

## Process identity and labels

- **Identity.** When a worker starts a job's command, it records the following in the table `job_procs`
  (`common/queue/identity.py`):
  - its own pid;
  - its process group (the worker leads its own session, so the group holds the whole job);
  - the start time of each process, from `/proc/<pid>/stat`;
  - the command's pid;
  - the code version (`common/queue/DEPLOYED_FROM`, else the git commit).
- **`cweq stop <id> [--grace N] [--why TEXT]`** stops one job. It works in this order:
  1. It checks that the recorded worker pid still has the recorded start time, so a reused pid is never signalled.
  2. It sends SIGTERM to the job's process group, then SIGKILL after the grace period.
  3. It removes every container of the job's compose projects, sidecars included.
  4. It marks the job `blocked`.

  Nothing is stopped by matching command lines.
- **Labels on processes.** Every process a worker starts carries `CWE_JOB_ID`, `CWE_KIND`, `CWE_TASK`, `CWE_BATCH`,
  `CWE_MODEL`, `CWE_RUN` and `CWE_CODE_VERSION`, and its children inherit them. `trial.py` also sets `CWE_TASK`,
  `CWE_MODEL` and `CWE_RUN` for each run it starts.
- **Labels on containers.** Every `main` container Harbor starts through `common/harbor_ext/cwe_reuse_env.py` (gate
  runs, trials, regrades) carries matching Docker labels: `cwe.job_id`, `cwe.kind`, `cwe.task`, `cwe.batch`,
  `cwe.model`, `cwe.run`, `cwe.code_version`, `cwe.started_by` (`cweq`, or `script` for other launchers) and
  `cwe.session`.
  - They come from one extra compose override (`common/harbor_ext/cwe_labels.py`) added to Harbor's compose file
    list. Harbor itself is unchanged.
  - `CWE_LABELS=0` turns them off.
- **`cweq orphans [--json]`** is read-only. It lists:
  - containers labelled with a job that is no longer running;
  - pipeline containers with no `cwe.*` labels;
  - processes carrying a queue job id whose job is no longer running.

## Schema

`jobs` (`common/queue/qdb.py`):

| Column | Meaning |
|---|---|
| `id` | integer key |
| `kind` | `build` `gate` `regate` `trial_run` `regrade` `rescore` `audit_prep` `audit_record` `fairness` `cleanup` `step3` `delivery_prep` |
| `task` | the slug, or a pseudo task |
| `args` | canonical JSON (sorted keys). `(kind, task, args)` is UNIQUE |
| `priority` | higher starts first. Effective priority = `priority + aging_per_hour × hours since queued_at` |
| `state` | `queued` → `leased` → `running` → `done` / `failed`; `blocked` = needs a person |
| `attempts`, `max_attempts` | starts so far; a stale worker or a retryable exit requeues until the attempts are used up |
| `owner_pid`, `lease_expires` | the worker wrapper (it leads its own session) and its lease |
| `depends_on` | JSON list of job ids that must be `done` first |
| `created`, `queued_at`, `started`, `finished` | UTC |
| `exit_code`, `result`, `log_path` | the script's exit code, its last output line (or why the job was blocked), and its log |
| `origin` | `reconciler` or `manual` |

Adoption adds two more tables:
- `adoptions`: one row per import, with its counts, conflicts and differences.
- `tasks`: each task's stage, next step and facts at the last adoption.

The event queue adds `events` (kind, task, payload, dedup key, urgent, state open or handled, action) and `marks` (the
last value seen per key).
The monitor adds `metrics` (one row per sample) and `monitor_alerts` (raised and cleared threshold crossings).

Exit codes:
- `0` → `done`.
- An exit code listed in `[retry_exit_codes]` → requeued, or blocked once the attempts are used up.
- Any other exit code → `failed` (use `cweq retry <id>`).

## CLI

```
python3 common/queue/cweq.py init
python3 common/queue/cweq.py adopt [--dry-run] [--detail]
python3 common/queue/cweq.py tasks [--stage S] [--next TEXT]
python3 common/queue/cweq.py reconcile [--once] [--dry-run] [--task SLUG]
python3 common/queue/cweq.py dispatch  [--once] [--dry-run [--with-reconcile]] [-v] [--skip-preflight]
python3 common/queue/cweq.py status
python3 common/queue/cweq.py enqueue KIND TASK [--args JSON] [--priority N] [--after ID]...
python3 common/queue/cweq.py retry ID          # also re-opens jobs blocked because this one failed
python3 common/queue/cweq.py block ID [--why TEXT]
python3 common/queue/cweq.py explain TASK      # what the rules see for the task, and all its jobs
python3 common/queue/cweq.py verify [--kind K] [--state S]   # post-condition checks of finished jobs (read-only)
python3 common/queue/cweq.py selfcheck [--tool regrade|rescore|all] [--run]   # reproduce a known grading
python3 common/queue/cweq.py events [--open] | events next | events handle ID --action TEXT
python3 common/queue/cweq.py inbox [--html PATH] [--json]
python3 common/queue/cweq.py delivered TASK NAME COMMIT [--date D] [--note TEXT]
python3 common/queue/cweq.py stop ID [--grace N] [--why TEXT]
python3 common/queue/cweq.py orphans [--json]
python3 common/queue/cweq.py monitor [--once] [--dry-run]   # machine samples, forecasts and alerts
python3 common/queue/cweq.py preflight       # read-only setup checks; exit 2 = critical
```

A job that exits with an ok code is `done` only when its post-condition check passes; every automatic rule, its
expected outcome and its check are listed in `docs/RULES.md`.

Options before the command: `--db PATH`, and `--config PATH` (or `$CWEQ_CONFIG`).
- `dispatch --dry-run --with-reconcile` answers "what would the queue do right now?". It copies the queue into memory,
  adopts and reconciles into the copy, and plans. It writes nothing.
- `pipelines/router/status_report.py` reads the queue for its status line: per kind, the running jobs, the work
  started outside the queue, and the queued jobs.

## Monitoring and preflight

**Resource monitor** (`common/queue/monitor.py`, `cweq monitor`). It samples the machine every minute into the
`metrics` table:
- CPU busy share, load, available memory and swap;
- free disk and inodes on the repository's file system, and `/tmp` inodes;
- Docker containers (all and running), images and build-cache size;
- running jobs per kind, with work started outside the queue shown as `+kind`.

The slow Docker reads run in the background, and each sample carries their last result:
- the image count (`docker images -q`), every 10 minutes;
- the build-cache size (`docker system df`, which can take many minutes on a large image store), every hour.

Each sample also carries a forecast:
- the disk burn rate in GB per hour, a least-squares fit over the last hour of samples;
- the hours until free disk reaches the admission floor at that rate;
- the same for inodes.

Thresholds in `[monitor]` turn crossings into rows of `monitor_alerts`: a `raised` row when a value crosses its
threshold, and a `cleared` row when it comes back. Nothing more is written while a value stays on the same side.

Two automatic effects:
- **Disk forecast.** When free disk is forecast to reach its floor within `disk_floor_within_h`, the monitor queues
  one extra `cleanup` job per UTC hour.
- **Admission.** The dispatcher's admission reads the latest sample while it is fresh.

Samples are kept for `retention_days`.

**Preflight** (`common/queue/preflight.py`, `cweq preflight`). Read-only checks of the machine's setup:
- the Docker daemon answers;
- `daemon.json`: shutdown timeout, open-file limit, container log rotation;
- the Docker client and compose timeouts, and BuildKit, in `common/gate/docker-tuning.env`;
- the local Harbor patches (`common/trial/harbor/README.md`);
- image reuse is wired in;
- gate limits and disk floors are set;
- model credentials are present (values are never read into the report);
- tool versions;
- disk, memory and inode headroom;
- the queue loops are running.

Each check reports OK, NEEDS APPLYING with the exact change, or CRITICAL. Changes that need root or a Docker restart
are reported, never applied. `cweq dispatch` refuses to start while a check is critical, unless it is given
`--skip-preflight`.

## Operations

Start (from the repository root, one of each):

```
setsid nohup python3 -I -u common/queue/cweq.py reconcile >> ~/.tb-graders/cwe/queue-logs/reconcile.log 2>&1 < /dev/null &
setsid nohup python3 -I -u common/queue/cweq.py dispatch  >> ~/.tb-graders/cwe/queue-logs/dispatch.log  2>&1 < /dev/null &
setsid nohup python3 -I -u common/queue/cweq.py monitor   >> ~/.tb-graders/cwe/queue-logs/monitor.log   2>&1 < /dev/null &
```

Run `cweq preflight` first; `dispatch` runs it itself and refuses to start on a critical result.

Taking over from per-batch schedulers:
1. Adopt (`cweq adopt --dry-run`, then `cweq adopt`) with zero conflicts.
2. Touch `pipelines/router/out/queue/<batch>.drain` for each scheduler. A draining scheduler starts nothing more and
   exits once the jobs it started have ended. Those jobs run in their own sessions and finish undisturbed.
3. Start the queue. From then on the queue starts every next step, including the gate and trials after a build the
   scheduler started. It counts the scheduler's remaining work against its limits.

Switching it off:
- **Stop new starts:** set `enabled = false` in `queue.toml`. The dispatcher still reaps stale workers but starts
  nothing. Each phase-4 kind also has its own switch under `[phase4]`.
- **Stop everything:** stop the `cweq.py dispatch` and `cweq.py reconcile` processes. Running workers finish their
  current script and record it.
- **One job:** `cweq block <id>`. The worker stops the script at its next lease refresh.
- **Back to per-batch schedulers:** remove the `.drain` files and restart each scheduler with its usual arguments.
  Schedulers detect running builds and trials, so nothing runs twice.
