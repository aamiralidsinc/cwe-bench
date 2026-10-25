# Stacking pipeline: guide

**One-line summary:** a stacked task hides several independent real bugs (the "concepts" or traps) behind one
reported advisory. Each stacked task has a one-bug twin, `<slug>-control`, whose `instruction.md` is
byte-identical (build rule 13). Both models must fail the stacked task 3/3, fairly, for it to count as a breaker.

- Versions of every component (current vs last proven, and where the old versions are): **COMPONENTS.md**.
- Design background: `docs/STACKING-EXPLORATION.md`.
- Shared infrastructure: `common/README.md`.

Run every command **from the repo root**: `~/cwe-bench` on the VM, or the checkout on the Mac. Agent steps go through
`common/launch/drive.sh <deepseek|mimo> bash <script> <args>`. The launcher sets `MODEL` and the endpoint, and
the scripts refuse to run without `MODEL`.

## Folders

| Folder | What is in it |
|---|---|
| `1-select/` | Phase 1 candidate selection (Mac): H4 ranking, H3 pairs, SZZ check, H1/H2 groups, reader jobs, reader (Opus), scorer + weights + calibration |
| `2-prepare/` | `build_prepare_stack.py`: fills `common/builder/TASK-BUILD-PROMPT-v1.md` + `STACKING-BUILD-ADDENDUM.md` into `build/<slug>/BUILD-PROMPT.md` |
| `3-build-gate/` | `run_stack_pipeline.sh` (the per-slug driver), `normalize_expect.py`, `check_stack.py` (static stacking rules, incl. rule 13) |
| `4-listing/` | the listing check: does the instruction list or describe hidden traps? Reviewer prompt v3, launcher, verdict, calibrator, `LISTING_ENFORCE` |
| `5-upgrade/` | the separate instruction-only upgrade step (no rebuild): launcher, batch runner, prompt |
| `6-trial/` | `stk_queue.py`: build phase and trial phase queue |
| `7-fairness/` | `run_fairness_stack.sh` + `STACKING-FAIRNESS-ADDENDUM.md` (appended to `common/fairness/FAIRNESS-REVIEW-BRIEF.md`) |
| `8-fairfix/` | `run_fairfix_stack.sh`: applies a fairness review, or an audit repair brief (`FAIRFIX_BRIEF`) |
| `out/` | run records: selection outputs, `batch1.txt`, reader records, queue logs, listing calibration, night logs |
| `archive/` | old versions, one-off scripts, the 2026-10-24/25 night chains (see `archive/README.md`) |

## Run order

```
[Mac]  1-select: screen -> H4/H3/SZZ -> reader jobs -> reader (Opus) -> score -> out/batch1.txt (chosen by hand)
[VM]   2-prepare -> 6-trial/stk_queue.py build (= 3-build-gate/run_stack_pipeline.sh per slug:
         build -> normalize -> check -> listing -> gate -> blind fix -> .sound -> control gate)
       (optional, separate) 5-upgrade: instruction-only rewrite of already-built tasks
       6-trial/stk_queue.py trial -> audit every graded run -> fairness after a model fails 3/3
       -> repair loop (fairfix / test fix, gate, re-trial) -> breaker review (NEEDS_HUMAN_REVIEW.md)
```

### Phase 1: selection (Mac; the candidate index exists only on the Mac)

1. Screen more hosts:
   `python3 -I common/screener/run_screener.py --pick 100`, then
   `CLAUDE_BIN=... python3 -I common/screener/run_screener.py --run --parallel 3 --model claude-opus-5-5`.
   Records go to `out/screener/`.
2. Rank and pair:
   - `python3 -I pipelines/stacking/1-select/h4_rank.py`
   - `h3b_pairs.py`
   - `szz_pairs.py`
   - (optional) `h12_groups.py`

   Their outputs are `out/h4_*`, `out/h3b_*`, `out/szz_*` and `out/h12_*`.
3. Reader jobs, then the reader (Opus 5.5 via Claude Code). **Regenerate the jobs before a new batch:** the batch-1
   `out/reader_jobs.jsonl` holds absolute paths from before the 2026-10-25 move.
   `python3 -I pipelines/stacking/1-select/make_reader_jobs.py --h4 9 --h3 12`, then
   `python3 -I pipelines/stacking/1-select/run_reader.py --parallel 2 --model claude-opus-5-5`.
   This writes `out/reader/<job>.json`.
4. Score: `python3 -I pipelines/stacking/1-select/score_stack.py`, which writes `out/stack_scores.{md,tsv}`.
5. **Choose the batch by hand.** `out/batch1.txt` holds the slugs in priority order; the build queue reads it. No
   script makes this file. Batch 1 was the 30 usable reader records in score order. Copy the new records and the
   batch file to the VM.

### Phase 2: build and gate (VM)

6. Prepare a prompt per job:
   `python3 -I pipelines/stacking/2-prepare/build_prepare_stack.py <job_id> --project-root ~/cwe-bench`.
   This writes `build/<slug>/BUILD-PROMPT.md`.
7. Build and gate the batch:
   `python3 -I pipelines/stacking/6-trial/stk_queue.py build --slugs-file pipelines/stacking/out/batch1.txt --slots 16`.
   For each slug this runs `3-build-gate/run_stack_pipeline.sh`. Run the steps in order:
   1. `common/launch/run_build.sh` (DeepSeek builder).
   2. `normalize_expect.py`.
   3. `check_stack.py`.
   4. The listing check, `4-listing/run_listing_check.sh` plus `listing_verdict.py`. With `4-listing/LISTING_ENFORCE`
      present, a FAIL withholds `.sound` and writes `.listing_fail`; otherwise it writes `.listing_warn` only.
   5. `common/gate/gate.py` (nop, oracle, patches).
   6. `common/blindfix/run_blindfix.sh`.
   7. The patches gate again.
   8. `.sound`.
   9. The control's gate.

   Stagger starts; the queue does this itself.

### Optional: instruction-only upgrade (no rebuild)

8. `bash pipelines/stacking/5-upgrade/upgrade_stack_batch.sh <slugs-file> 6` runs
   `common/launch/drive.sh deepseek bash pipelines/stacking/5-upgrade/run_upgrade_stack.sh <slug>` for each slug, 6 at a time.
   - **Order:** snapshot the control, then the task; the agent rewrites only `instruction.md` (two rounds, guided
     by the listing check); copy it to the control; static gate on both.
   - **On success:** it writes `.upgraded`, and the new version is re-trialled from zero.
   - **Exit codes:** 0 ok; 1 not finished; 2 refused; 3 unchanged; 4 touched other files; 5 listing still FAIL.
   - **After any upgrade, check for contradictions before trialling** (see "Lessons").

### Phase 3: trial, audit, fairness, repair

9. Trials: `python3 -I pipelines/stacking/6-trial/stk_queue.py trial --slots 16`.
   - It refuses to start while any build runs, skips pairs already decided, runs stacked tasks first and controls
     last, and uses 3 runs per model with early abort.
   - Under the hood it calls `common/trial/trial.py <slug> --models <m> --no-verdict --first-run N --max-runs K`.
   - A single extra pair can be started directly with `python3 common/trial/trial.py ...`.
   - **The queue does not skip pairs that are already running.** Check running trials first (`ps`, or `/proc`)
     before restarting it.
10. **Audit every graded run** (a manual or agent step; no script):
    1. `python3 common/audit/postmortem.py pending` lists the runs that need an audit.
    2. `postmortem.py prepare <trial_dir>` writes an `AUDITOR_BRIEF.md` folder.
    3. One **Opus 5.5 (high effort)** sub-agent per folder writes `verdict.json`. Give each auditor its own scratch
       folder.
    4. `postmortem.py record-ready`.
    5. Read verdicts **only** from `python3 common/audit/audit_results.py`, which writes `build/audit/ledger.md`.

    Audit failing runs first; a solve cannot make a breaker.
11. Fairness: run it only after a model fails 3/3 with every run audited:
    `common/launch/drive.sh deepseek bash pipelines/stacking/7-fairness/run_fairness_stack.sh <slug>`, then
    `python3 common/fairness/fairness_verdict.py <slug>` (READY / NOT_READY / ERROR).
    If NOT_READY, an Opus leniency validation decides whether the defect is real (the DeepSeek reviewer sometimes
    confuses lenient with unfair).
12. Repair loop, used when an audit finds a test fault or a fairness review is NOT_READY:
    1. `touch build/<slug>/hold_deepseek build/<slug>/hold_mimo` (the trial runner then refuses new runs).
    2. Write `build/<slug>/AUDIT-FIX-<date>.md` with a numbered "Required changes" list.
    3. `FAIRFIX_BRIEF=build/<slug>/AUDIT-FIX-<date>.md common/launch/drive.sh deepseek bash pipelines/stacking/8-fairfix/run_fairfix_stack.sh <slug>`.
       It snapshots, bumps `VERSION`, has the agent self-gate, restores on failure, copies a changed instruction to
       the control, and re-runs the listing check.
    4. `bash common/gate/gate_one_ds.sh <slug>` (and the control).
    5. Remove the holds and re-trial from run 1.

    A test fix that cannot change any existing verdict may be made **in place** without a version bump: back up the
    file to `build/<slug>/testfix-<date>/` and re-gate.
13. Breaker = both models 0/3, every failing run audited trustworthy, and fairness READY. Write
    `build/<slug>/NEEDS_HUMAN_REVIEW.md` and **never commit or ship a breaker without a human decision**.

## Re-gate rule: any change to what the gate tests invalidates the gate (enforced)

A `.sound` proves the task only for the exact files it gated. **Whenever a task's `tests/`, `solution/`,
`environment/` or `build/<slug>/checks/` change after its gate pass** (fairfix, testfix, upgrade, a hand repair,
a test removed as unfair), do all of this, in order:

1. **Re-gate the whole task**: `bash common/gate/gate_one_ds.sh <slug>` (nop, oracle and every patch check, not
   only the changed tests). A changed test can make a wrong-fix patch pass or the reference fail.
2. **Re-grade the saved runs** on the new tests: `common/audit/regrade.py` (needs the run's container or final
   code), or `common/audit/rescore_from_results.py` when the repair only **removes** tests. A repair that changes
   what a test accepts cannot be rescored from results: it needs the code, or new runs.
3. **Re-audit** every failing run whose reward changed (a same-reward regrade keeps its audit).
4. An **instruction** change is different: the gate does not read `instruction.md`, so it needs no re-gate, but
   it needs a **re-trial** (the runs saw the old text).

Enforcement: `gate_one_ds.sh` writes `build/<slug>/gate_fingerprint.json` when a task is SOUND
(`common/gate/fingerprint.py`). `common/trial/run_trial.sh` and `common/audit/regrade.py` refuse to start when the
files no longer match (exit 3 / refusal), and say to re-gate. Tasks gated before 2026-10-25 have no fingerprint
and only get a warning; electron-builder-ds, hubuum-client-rust-ds and mockoon-ds are known to need a re-gate
(their deciding tests came with the 2026-10-20 upgrade, after their `.sound`).

## Marker and state files (in `build/<slug>/` unless noted)

| File | Written by | Read by | Meaning |
|---|---|---|---|
| `.sound` | `run_stack_pipeline.sh`, `gate_one_ds.sh` | `stk_queue.py trial`, upgrade (precondition) | gated, trial-eligible |
| `.unsound` / `.gate_error` / `gate_verdict.json` | `gate_one_ds.sh` | operator | task failure / infrastructure failure |
| `.listing_fail` / `.listing_warn` | `run_stack_pipeline.sh`, upgrade exit 5 | `stk_queue.py build` (skips) | listing check failed (enforced / advisory) |
| `listing.json`, `listing_status.txt` | `run_listing_check.sh` | `listing_verdict.py` | the reviewer's NAMED/DESCRIBED/GENERAL/ABSENT labels |
| `LISTING_WAIVER.md` | human | humans (no script reads it) | listing FAIL accepted by the user (comfyui, fabio, pyload-7gvf) |
| `.upgraded` | `run_upgrade_stack.sh` | operator | instruction upgraded ("vN UTC") |
| `VERSION` | `common/versioning/snapshot_experiment.sh` | trial runs, snapshots | task version (unchanged by in-place test fixes) |
| `hold_deepseek`, `hold_mimo` | operator, chains | `common/trial/run_trial.sh` (exit 3) | no new trial runs for that model |
| `FAIRNESS.md`, `fairness_status.txt` | `run_fairness_stack.sh` | `fairness_verdict.py` | fairness review |
| `AUDIT-FIX-<date>.md` | operator / Opus | `run_fairfix_stack.sh` via `FAIRFIX_BRIEF` | repair brief |
| `NEEDS_HUMAN_REVIEW.md` | operator | humans | breaker candidate with the open question and the user's decision |
| `~/.tb-graders/cwe/experiments/<slug>/vN-<UTC>/` | `snapshot_experiment.sh` | `restore_snapshot.sh` | each earlier version and its trial runs |
| `pipelines/stacking/4-listing/LISTING_ENFORCE` | `listing_calibrate.py --enforce` | `run_stack_pipeline.sh` | global switch: listing FAIL blocks `.sound` |

## Rules and decisions that govern this pipeline

- **Fairness runs after the trial**, and only after a full 3/3 fail. One fail can be a fluke.
- **A 3-hour timeout counts as a model fail.** Re-run a 2-hour timeout at 3 hours (`CWE_AGENT_TIMEOUT_MULT=1.5`).
- **Instruction/test contradiction:** keep the instruction, and change the tests and reference so that upstream's
  fix becomes a wrong fix (the "harder resolution").
- **Tests never call original product functions.** A fixture models the behaviour, and a fixture-made method is
  fine when it models a real sink.
- **Trap listing can only be judged by an LLM** (the listing check), never deterministically.
- **The upgrade step stays separate** from `run_stack_pipeline.sh`. Fixes go into the right component, never
  into an upgraded `instruction.md` by hand.
- **Breaker classes seen so far:**
  - "real bug outside the advisory and the upstream fix" (`uncovered_upstream`), recorded in
    `build/audit/UNCOVERED-UPSTREAM-CLASS.md`;
  - keep-working regressions (mistral-rs, lemur; confirm with Klavis).

## Lessons from batch 1 (2026-10-23..25)

- **The v1 upgrade prompt damaged 11 of 22 instructions.** It deleted exceptions instead of rewording rules.
  Prompt v2 (rule 3) is the fix, but **v2 has not run yet**. After any upgrade, run a contradiction check
  before trials.
- **Under heavy load harbor refused trials at ~37 s.** Its 30 s nftables probe timed out. Fixed by
  `common/trial/harbor/patch_probe_timeout.sh`; re-apply it after any harbor reinstall.
- **A stub or fixture in a test harness can break a correct fix.** Examples: senaite `_StubApi`, the jenkins
  non-serialisable realm. Check the harness first when an audit reports "test fault".
- **A control built for only one of two reported problems** is easier than its own instruction (senaite-control).
  When a report names two problems, the control needs both.

## Known gaps (not yet fixed in code)

- **Two gate routes both write `.sound`.** The build path calls `common/gate/gate.py` directly; every repair path
  calls `common/gate/gate_one_ds.sh`.
- **`LISTING_WAIVER.md` and the listing check after a fairfix are not enforced by any script.** The operator
  checks them.
- **No script exists for:** `stk_queue.py trial` skipping running pairs, the batch choice (`batch1.txt`), the audit
  launcher, leniency validation, or the breaker record.
- **The newest driver (`run_stack_pipeline.sh` with the listing step) and build addendum v2+ have never run a
  build.** Batch 1 was built with the versions in `archive/versions/` (see COMPONENTS.md).
