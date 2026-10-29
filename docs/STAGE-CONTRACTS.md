# Stage contracts

Every pipeline stage reads and writes the task folder `build/<slug>/`. This document names those files and markers,
says which stage writes and reads each one, and states each stage's success condition, so a stage can be changed or
added without breaking the next one.

- **Marker library:** `common/markers.py` (names, meanings, readers and atomic writers; `python3 common/markers.py
  table` prints the table below). Shell twin: `common/markers.sh`.
- **Contracts, machine-readable:** `common/stage_contracts.toml`.
- **Checker:** `python3 common/markers.py check <slug> [<slug> ...]` or `check --all [--json] [--min warn]` reports
  folders that break the contracts. It reads only. Exit 2 when an error is found.

## Markers

| Marker | Kind | Meaning | Written by | Read by |
|---|---|---|---|---|
| `.sound` | flag | The task gated SOUND on its current files and is ready for trials. | common/gate/gate_one_ds.sh (on pass), common/gate/postbuild.sh and regate.sh (final), a listing waiver | taskstate.py, scale_queue.py, phase3/4, trial launchers, status_report.py |
| `.unsound` | flag | A gate stage failed on the task itself (deterministic). No trials. | common/gate/gate_one_ds.sh | taskstate.py, scale_queue.py, reconcile.py |
| `.gate_error` | flag | The gate kept failing on infrastructure; not a task verdict. | common/gate/gate_one_ds.sh | taskstate.py, scale_queue.py, reconcile.py |
| `.gate_passed` | flag | The gate passed but the post-gate steps (blind patch, fingerprint, listing) have not finished; trials must not start yet. Left behind only when a post-build or re-gate stopped early. | common/gate/postbuild.sh, regate.sh | taskstate.py, scale_queue.py, reconcile.py |
| `.listing_fail` | flag | Stacking only: the instruction lists hidden traps after the allowed rewrites; not sound unless LISTING_WAIVER.md says otherwise. | common/gate/postbuild.sh, regate.sh | taskstate.py, scale_queue.py, inbox.py |
| `.listing_warn` | flag | Stacking only: listing check failed while enforcement was advisory. | common/gate/postbuild.sh, regate.sh | people |
| `.blind_fail` | flag | The blind fix's patch did not pass; kept as checks/blind.failed.patch. Not blocking. | common/gate/postbuild.sh, regate.sh | people, lint |
| `gate_fingerprint.json` | record | What the last SOUND gate covered (sha256 of tests, solution, environment, checks); a different digest means the gate is stale. | common/gate/fingerprint.py write (via gate_one_ds.sh / postbuild.sh / regate.sh) | run_trial.sh, regrade tools, taskstate.py, reconcile.py, phase3.py |
| `postbuild.log` | log | Post-build and re-gate log; its last `RESULT:` line is the gate outcome. | common/gate/postbuild.sh, regate.sh, repair and waiver steps | reconcile.py, checks.py, people |
| `.hold-repair` | flag | A test repair is between its edit and its regrades: no new trials of the task. | repair steps (people / repair scripts), the queue after a held re-gate | taskstate.py, dispatch.py, scale_queue.py, phase4.py |
| `hold_{model}` | flag | No new runs of this model on this task. When its text says the model was blocked (or {MODEL}-BLOCKED.md exists), the ledger shows that model as blocked. | people | common/trial/run_trial.sh, trial.py, phase3.py, dispatch.py |
| `repaired-tests-*` | folder | Originals (*.orig) and README.md of tests changed by a repair. | repair steps | reconcile.py (R1-R4), people |
| `removed-tests-*` | folder | Originals and README.md of tests removed by a repair. | repair steps | reconcile.py (R1-R4), people |
| `history` | folder | Records of the steps after the build (fairfix, upgrade, test repair, regrade), one file each (<YYYYMMDD>-<kind>.md), so notes.md keeps build facts only (2026-10-28). | fairfix and upgrade agents, repair steps, people | people (never the fairness reviewer or the auditor) |
| `notes.for-review.md` | record | The build notes without earlier conclusions, regenerated before each fairness review (common/util/notes_filter.py); the reviewer reads it instead of notes.md. | pipelines/sibling/9-fairness, pipelines/stacking/7-fairness | the fairness reviewer |
| `BUILD-PROMPT.md` | record | The builder's prompt for this task. | common/builder/build_prepare.py | common/launch/run_build.sh, phase3.py |
| `start_utc.txt` | record | UTC start of the last build. | common/launch/run_build.sh | taskstate.py, scale_queue.py |
| `end_utc.txt` | record | UTC end of the last build (written when the builder exits, whatever the outcome). | common/launch/run_build.sh, resume_pipeline.sh | taskstate.py, scale_queue.py, orphan_builder_guard.sh |
| `build-exit.txt` | record | Exit code of the last builder run. | common/launch/run_build.sh | run_pipeline.sh, run_stack_pipeline.sh, checks.py |
| `resume_start_utc.txt` | record | UTC start of the last resumed builder session (resume_pipeline.sh). | pipelines/sibling/6-build/resume_pipeline.sh | common/util/agent_status.py, markers.build_paused |
| `build_status.json` | record | agent_status.py details of the last builder run (exit code, result, wall_sec / limit_sec / paused_interrupt for an exit 124). | common/util/agent_status.py (via the build pipelines) | markers.build_paused, people |
| `pipeline.log` | log | Sibling build log; STOP / BUILD-INCOMPLETE / stopped/failed lines end a build. | pipelines/sibling/6-build/run_pipeline.sh | taskstate.py, scale_queue.py |
| `stack_pipeline.log` | log | Stacking build log; same end lines as pipeline.log. | pipelines/stacking/3-build-gate/run_stack_pipeline.sh | taskstate.py, scale_queue.py |
| `runs_{model}.log` | log | One line per run of the current task version (`reward=`), moved away with each new version. | common/trial/trial.py | common/trial/trial_state.py, taskstate.py |
| `FAIRNESS.md` | record | The fairness review; its GATE_A line is the verdict, its CONFLICTS line the tests that disagree with the instruction (since 2026-10-28). | pipelines/sibling/9-fairness, pipelines/stacking/7-fairness | common/fairness/fairness_verdict.py, inbox.py, delivery.py, export_delivery.py |
| `fairness_status.txt` | record | Whether the last fairness run finished (`ok ...`). | pipelines/sibling/9-fairness, pipelines/stacking/7-fairness | common/fairness/fairness_verdict.py |
| `HUMAN-DECISION.md` | record | The owner's decision (DECISION: KEEP|REPAIR|DROP, DATE:), the ruling on deciding conflicts (CONFLICTS-RULED: <date> <KEEP|DROP|REPAIR> <reason>), client-audit outcomes (CLIENT-AUDIT:) and, after a delivery, a DELIVERED: line. | people; `cweq delivered` | fairness_verdict.py, taskstate.py, delivery.py, inbox.py |
| `LISTING_WAIVER.md` | record | The owner's decision to trial a stacking task despite the listing check. | people | people, this checker |
| `lint` | folder | Task-quality lint results, one JSON per gate version. | common/queue/lintstep.py | cweq explain, inbox.py |

## Stages

| Stage | Script | Reads | Writes | Success |
|---|---|---|---|---|
| build | common/launch/run_build.sh (via pipelines/sibling/6-build/run_pipeline.sh or pipelines/stacking/3-build-gate/run_stack_pipeline.sh) | BUILD-PROMPT.md | start_utc.txt; end_utc.txt; build-exit.txt; build-run.json; build_status.json; pipeline.log | stack_pipeline.log; tasks/<slug>/; checks/; manifest.json | end_utc.txt not older than start_utc.txt, builder status ok, at least 5 task files; then the post-build checks run |
| build_resume | common/queue/kinds/build_resume.py -> pipelines/sibling/6-build/resume_pipeline.sh | build-exit.txt (124); build_status.json; end_utc.txt; the builder session in ~/.claude/projects | resume_start_utc.txt; end_utc.txt; build-exit.txt; build-run.json; build_status.json; pipeline.log | tasks/<slug>/ | the resumed builder ran after the job started and the build has an outcome (gate marker or a resumed-build log line); only for a build cut by its overdue timer after a pause (markers.build_paused) |
| gate | common/gate/gate_one_ds.sh | tasks/<slug>/; checks/; manifest.json | exactly one of .sound | .unsound | .gate_error; gate_fingerprint.json (only with .sound; removed otherwise); gate_report*.json; evidence/ | .sound with a gate_fingerprint.json matching the gated files |
| postbuild | common/gate/postbuild.sh | .sound (from the gate); checks/blind.patch; listing.json (stacking) | .gate_passed (while the post-gate checks run); .blind_fail; .listing_warn; .listing_fail; .sound; gate_fingerprint.json; postbuild.log RESULT line | last postbuild.log RESULT is SOUND and .sound is present; .gate_passed is gone |
| regate | common/gate/regate.sh [--listing] | checks/blind.patch (reused); listing.json (reused); tasks/<slug>/ | .gate_passed (transient); .sound | .unsound | .gate_error | .listing_fail; .blind_fail; gate_fingerprint.json; postbuild.log RESULT line | a RESULT line newer than the start and a marker that matches it |
| blind_fix | common/blindfix/run_blindfix.sh | tasks/<slug>/instruction.md; the task image | checks/blind.patch; blind_status.txt | checks/blind.patch exists and passes the patch check (otherwise checks/blind.failed.patch + .blind_fail, not blocking) |
| listing_check | pipelines/stacking/4-listing/run_listing_check.sh + listing_verdict.py; rewrites: pipelines/stacking/5-upgrade/run_upgrade_stack.sh | tasks/<slug>/instruction.md; manifest.json (traps) | listing.json; listing_status.txt; .listing_fail | .listing_warn (through postbuild.sh / regate.sh) | listing_verdict.py exit 0; at most 3 tries (build + 2 rewrites), then the owner decides (LISTING_WAIVER.md to trial, or drop) |
| test_repair | people / repair scripts; follow-up by the work queue (reconcile rules R1-R4) | tasks/<slug>/tests/ | repaired-tests-<date>/ or removed-tests-<date>/ (originals + README.md); .hold-repair (until the regrades are in); tasks/<slug>/tests/ (one atomic copy) | re-gate SOUND on the changed files, every graded run regraded or rescored, .hold-repair released |
| trial | common/trial/trial.py -> common/trial/run_trial.sh | .sound; gate_fingerprint.json (must be current); hold_<model>; .hold-repair (queue) | runs_<model>.log (one line per run); ~/.tb-graders/cwe/jobs/<job>/<trial>/ | the runs log gained the planned run numbers |
| audit_prep | common/audit/postmortem.py prepare | trial folder; tasks/<slug>/; build notes | <trial>/postmortem-<UTC>/ (AUDITOR_BRIEF.md, PREPARED.json, evidence/) | a new PREPARED.json |
| audit_record | common/audit/postmortem.py record-ready + audit_results.py | <trial>/postmortem-*/verdict.json | build/audit/ledger.md; build/audit/trials.tsv | ledger and trials.tsv rewritten after the start |
| fairness | pipelines/sibling/9-fairness/run_fairness.sh | pipelines/stacking/7-fairness/run_fairness_stack.sh | tasks/<slug>/; audited runs | FAIRNESS.md; fairness_status.txt | FAIRNESS.md newer than the start, fairness_status.txt ok, a GATE_A READY or NOT_READY verdict |
| decision | people (the owner); `cweq delivered` appends the DELIVERED line | FAIRNESS.md; audited ledger | HUMAN-DECISION.md (DECISION, DATE, WHY; DELIVERED after the push); LISTING_WAIVER.md | a dated DECISION line; DELIVERED only after KEEP |
| delivery_prep | common/queue/delivery.py (export_delivery.py) | HUMAN-DECISION.md (KEEP, CONFLICTS-RULED, CLIENT-AUDIT); FAIRNESS.md (NEEDS_HUMAN_REVIEW, CONFLICTS); gate_report.json (conflict_proven); build/audit/delivered.tsv; counted runs | ~/.tb-graders/cwe/deliveries/<UTC>-<slug>/ (tasks/, trajectory/, ready.json) | ready.json with ready=true and a clean secret scan; refused (exit 3, reasons in ready.json) without DECISION: KEEP, when the newest CLIENT-AUDIT line is not a KEEP, with an unrepaired conflict_proven test, with an open NEEDS_HUMAN_REVIEW and a stale KEEP, or with a deciding conflict and no current CONFLICTS-RULED: <date> KEEP line |
| lint | common/queue/lintstep.py (common/lint/task_lint.py) | tasks/<slug>/tests/; gate_fingerprint.json | lint/<fp16>.json | lint/<fp16>.json for the current gate version (warning-only; never blocks) |
| cleanup | common/util/hourly_cleanup.sh once | .hold-repair (held tasks keep their containers and images) | build/audit/hourly_cleanup.log | a `pass done` line |

## What the checker reports

| Code | Severity | Meaning |
|---|---|---|
| `verdict-not-exclusive` | error | More than one of `.sound`, `.unsound`, `.gate_error` |
| `listing-fail-and-sound` | error | `.listing_fail` and `.sound` without `LISTING_WAIVER.md` |
| `sound-stale` | error | `.sound`, but the task's files changed since the SOUND gate: re-gate before any trial |
| `fingerprint-unreadable` | error | `gate_fingerprint.json` cannot be read |
| `decision-unparseable` | error | `HUMAN-DECISION.md` without a `DECISION:` line |
| `delivered-without-keep` | error | A `DELIVERED:` line on a decision that is not KEEP |
| `gate-passed-left`, `gate-passed-and-sound` | warn | A post-build or re-gate stopped between the gate and its result |
| `fingerprint-orphan` | warn | A fingerprint without `.sound` or `.hold-repair` |
| `result-sound-no-marker`, `sound-but-result-not-sound` | warn | The last `RESULT:` line and the markers disagree |
| `end-without-start` | warn | `end_utc.txt` without `start_utc.txt` |
| `decision-undated` | warn | `HUMAN-DECISION.md` without a `DATE:` line |
| `repair-without-readme`, `hold-without-repair` | warn | A repair folder without its README, or a hold without a repair |
| `sound-legacy`, `build-running-or-cut`, `model-held`, `blind-fail`, `listing-waived` | info | State worth knowing, not a violation |

## Where the library is used

Every reader and writer of a task-folder marker goes through the library: `common/markers.py` in Python,
`common/markers.sh` in shell.

- **Python readers**
  - `common/queue/taskstate.py`: build state, flags, fingerprint version, delivered line. The decisions inbox
    (`inbox.py`), the lint step (`lintstep.py`) and `cweq.py` read task state through it.
  - `common/queue/checks.py`: post-condition checks (last gate result, gate markers, fingerprint, build start and
    end, holds, runs log).
  - `common/queue/phase4.py` (repair holds), `common/queue/delivery.py` (the DELIVERED line, written atomically),
    `common/queue/reconcile.py` (last gate result).
  - `common/trial/trial.py` (holds, runs log), `common/trial/trial_state.py` (runs log),
    `common/fairness/fairness_verdict.py` (owner decision).
  - `pipelines/router/scale_queue.py` (build done, sound), `pipelines/router/status_report.py` and
    `scale_ledger.py` (gate state, build start and end), `pipelines/stacking/6-trial/stk_queue.py` (sound,
    listing hold).
- **Shell helpers** (`common/markers.sh`)
  - `cwe_mark`, `cwe_unmark`, `cwe_gate_verdict`, `cwe_hold_after_gate`, `cwe_mark_sound`, `cwe_mark_listing_fail`:
    flag writes.
  - `cwe_write_atomic`, `cwe_stamp`: record files written atomically (`start_utc.txt`, `end_utc.txt`,
    `build-exit.txt`, `.upgraded`).
  - `cwe_has`, `cwe_read`, `cwe_tasks_with`: readers.
- **Shell scripts**
  - `common/gate/gate_one_ds.sh`, `postbuild.sh`, `regate.sh`: the gate verdict, the hold after the gate, blind and
    listing flags, final sound.
  - `common/launch/run_build.sh`, `pipelines/sibling/6-build/run_pipeline.sh`, `resume_pipeline.sh`: build start,
    end and exit records.
  - `pipelines/stacking/3-build-gate/run_stack_pipeline.sh`, `pipelines/stacking/5-upgrade/run_upgrade_stack.sh`:
    listing hold and sound.
  - `common/trial/run_trial.sh`: model holds.
  - `common/util/orphan_builder_guard.sh` (build end), `hourly_cleanup.sh` (repair holds),
    `common/versioning/restore_snapshot.sh` (gate flags restored with a snapshot).
