# Stacking pipeline (Phase 1 tooling), 2026-10-22

**Design:** `../STACKING-EXPLORATION.md`.

**Phase 1 runs locally and needs no VM.** Phase 2, building and trialling tasks, needs a VM with
Docker.

| Step | File | What it does | Status |
|---|---|---|---|
| 1a | `h4_rank.py` | ranks the screened hosts for H4 stacking (several real routes of different kinds; at least one DeepSeek-type and one MiMo-type) → `out/h4_candidates.tsv`, `out/h4_shortlist.md` | done: 150 records, 9 unbuilt hosts offer both types |
| 1b | `h3b_pairs.py` | resolves "incomplete fix / bypass / regression of CVE-…" advisory pairs to repo and fix commits → `out/h3b_pairs.tsv`, `out/h3b_summary.md` | done: 455 pairs, **148 ready**, 23 dropped as same-fix-commit |
| 1c | `szz_pairs.py` | SZZ check of each ready pair: does the later fix change code the earlier fix wrote? (H3a regression vs H3b incomplete) → `out/szz_pairs.tsv`, progress in `out/szz_run.log` | running (resumable); blobless clones in `~/.tb-graders/cwe/stacking/clones/` |
| 1d | `h12_groups.py` | co-present advisories per package, split by fixed together (H1) or separately (H2) → `out/h12_groups.tsv`, `out/h12_summary.md` | done: 916 mid-size groups (H2 652, mixed 213, H1 51) |
| 2 | `STACKING-READER-PROMPT.md` | per candidate: traps with mechanism, locations, tier per model, type; shared-guard groups; history; conflicts; fairness risks; chosen design → `out/reader/<id>.json` | written; not run yet |
| 3 | `score_stack.py` + `stacking_weights.json` | probabilistic score on D1-D3, plus flags (missing DeepSeek-type or MiMo-type trap, single concept, single trap carries, fairness risk) → `out/stack_scores.*` | done; passes the calibration check (`calibration/`: sib2 0.59 > sib 0.02 > prompty 0.008, flags match) |
| 4 | `STACKING-BUILD-ADDENDUM.md` | the stacking rules appended to the build prompt: 3+ independent concepts, both model types, no single carry, history rules (H3 pin and first-fix check, masking, conflicting fixes, dependency bumps), recall check, a one-bug control task | written |
| 5 | `check_stack.py` | static conformance check of a built stacked task's MANIFEST (`stacking` block, concepts, types, per-concept wrong-fix patches, recall patches, coupled tests, control task), plus one instruction check: the control's instruction.md must equal the stacked task's (rule 13, added 2026-10-24). It does not judge instruction wording | done; tested on good and bad manifests |
| 5b | `STACKING-LISTING-CHECK.md`, `run_listing_check.sh`, `listing_verdict.py` | post-build listing check (build rule 7): a read-only reviewer labels each hidden trap NAMED / DESCRIBED / GENERAL / ABSENT against instruction.md; FAIL on any NAMED or more than one DESCRIBED hidden trap (`advisory_route` traps exempt) | added 2026-10-24; verdict tested on the batch-1 audit (29 of 30 FAIL, as audited). **Advisory until calibrated:** without `stacking/LISTING_ENFORCE` a FAIL only writes `.listing_warn`; `listing_calibrate.py` compares the reviewer with the audit and creates the file (`--enforce`) when every verdict matches and at most 10% of hidden traps are labelled more leniently |
| 6u | `STACKING-UPGRADE-PROMPT.md`, `run_upgrade_stack.sh`, `upgrade_stack_batch.sh` | SEPARATE upgrade step for already-built stacked tasks (not part of `run_stack_pipeline.sh`): snapshot control + task, the agent rewrites ONLY instruction.md to pass the one-bug test (2 rounds max, guided by the listing reviewer), copy to the control (rule 13), static gate on both, listing check; no rebuild, no container gate. Re-trial afterwards with `stk_queue.py trial` | added 2026-10-24 |

**Also in Phase 1:**
- **Step 2 runners:** `make_reader_jobs.py` builds `out/reader_jobs.jsonl`; `run_reader.py` runs
  the reader on it (see "Running the reader" below).
- **`STACKING-FAIRNESS-ADDENDUM.md`:** the coupled, shape, fixture, independence, history, contract
  and decisive-test checks for stacked tasks, plus the fairfix rules. It is appended to the fairness
  brief and the fairfix prompt by `run_fairness_stack.sh` and `run_fairfix_stack.sh`.

## H3 sub-pattern names (renamed 2026-10-22)

| Name | Meaning (SZZ result) | Old label |
|---|---|---|
| H3a | regression: the later fix changes code the earlier fix wrote (≥50% of its changed lines) | H3a-regression |
| H3b1 | incomplete fix; the later fix touches some of the earlier fix's code | H3b-touching |
| H3b2 | incomplete fix; the later fix adds protection elsewhere | H3b-elsewhere |
| H3u | unclassified: the later fix only adds code, so SZZ cannot attribute it; read by hand | add-only |

SZZ is the Śliwerski-Zimmermann-Zeller method (2005, "When Do Changes Induce Fixes?"): blame the
lines a fix changes to find the commits that introduced them.

## Growing the H4 pool (approved 2026-10-22)

`run_screener.py` runs the **unchanged** sibling screener prompt (`builder/SCREENER-PROMPT-v2.md`,
read as is) on more advisories.
- **Selection:** the next 100 candidates by index score, one per repo, skipping hosts already
  screened or built, DoS-only advisories, and repos over 1.5 GB.
- **Records** are written to `out/screener/`, never to `sourcer/review/`.
- **The pinned commit** is the parent of the earliest fix commit; the index rarely stores it.
- **`h4_rank.py --recs`** reads both record folders (the default).

## Separation from the sibling-injection pipeline (approved 2026-10-22)

**No sibling-pipeline file is edited.** Everything new or adapted lives in this folder. On the
stacking VM, stacked tasks use the slug prefix `stk-`, and their controls end in `-control`.

| Kind | Pieces |
|---|---|
| **Built new (here)** | `h4_rank.py`, `h3b_pairs.py`, `szz_pairs.py`, `h12_groups.py`, `make_reader_jobs.py`, `run_reader.py`, `STACKING-READER-PROMPT.md`, `score_stack.py`, `stacking_weights.json`, `STACKING-BUILD-ADDENDUM.md`, `check_stack.py`, `STACKING-FAIRNESS-ADDENDUM.md`, the listing check (`STACKING-LISTING-CHECK.md`, `run_listing_check.sh`, `listing_verdict.py`), `run_stack_pipeline.sh` (driver); still to build: the stacked-vs-control analysis and the weights refit |
| **Reused as is** | OSV dumps and screener-v2 records (read-only); `builder/TASK-BUILD-PROMPT-v1.md`, `builder/templates/`, `conformance_check.py`, `builder/gate.py`; `run_build.sh`, `drive.sh`, `run_blindfix.sh`; `harness/run_trial.sh`, `build/trial.py`, **`pipeline/trial_set.sh`** (run with the pattern `stk-*`); `build/postmortem.py`; `builder/FAIRNESS-REVIEW-BRIEF.md`; `pipeline/trial_summary.py` |
| **Copied here and adapted** (originals untouched) | `build_prepare_stack.py`, from `sourcer/rerank-v4-draft/build_prepare.py`: it fills the build template from the reader record and appends the stacking addendum. `run_fairness_stack.sh`, from `run_fairness.sh`: it appends the fairness addendum, and the project root comes from `$HOME`. `run_fairfix_stack.sh`, from `run_fairfix.sh`: the same changes. |

**Trial policy (approved 2026-10-22): stop at the first solve.** Each model runs one trial at a time
and stops at its first solve; it gets all 3 runs only while it keeps failing. The two models run
independently. This is what `trial_set.sh` / `build/trial.py` already do. A task is a breaker only
when both models fail 3/3.

**Decisions (2026-10-22):**
- **Phase 2 builder model: DeepSeek V4.1 Flash**, via the VM's `drive.sh deepseek`.
- DeepSeek-built tasks used to describe sibling surfaces in their instructions. The guards are the
  template's no-surface rule, the addendum (rules 5, 7, 10, v2 of 2026-10-24), fairness S1 (v2) and
  the listing check (step 5b). `check_stack.py` is NOT one of them: it does not judge instruction wording.
  (`BETTER-PATTERNS.md` is a local design note, not deployed to the VM.)
- **Batch 1 listed its traps** (2026-10-23 audit, `out/listing_audit.json`): 137 of 155 traps had a
  sentence of their own in instruction.md. The addendum v1 rules 5 and 10 and fairness S1 v1 asked
  for a stated value per hidden route, which overrode rule 7.
- The reader (step 2) runs locally with Claude Code.

## Running the reader (step 2)

1. Build the job list (re-run it after the SZZ miner finishes, so its results order the H3 pairs):

       python3 -I stacking/make_reader_jobs.py --h4 9 --h3 12

2. Optional dry run: clones, pins, worktrees and filled prompts, with no model call:

       CLAUDE_BIN=/Users/dev/.nvm/versions/node/v24.19.0/bin/claude python3 -I stacking/run_reader.py --dry-run

3. Run it, in a plain terminal (not inside a chat):

       CLAUDE_BIN=/Users/dev/.nvm/versions/node/v24.19.0/bin/claude python3 -I stacking/run_reader.py --parallel 3 --model claude-opus-5-5

**Outputs:** `stacking/out/reader/<id>.json` (one per candidate), `<id>.run.json` (the CLI's own
output) and `_run.log` (progress: one start and one finish line per job). Jobs that already have an
output are skipped, so re-running resumes.

4. Score: `python3 -I stacking/score_stack.py`, giving `stacking/out/stack_scores.md`.

**Run, in order:**
1. `h4_rank.py --built <tasks dirs>`, `h3b_pairs.py`, `szz_pairs.py`, `h12_groups.py`;
2. the reader prompt on the shortlists;
3. `score_stack.py`;
4. build with the build prompt plus the addendum;
5. `check_stack.py SLUG`, the listing check (`run_listing_check.sh` + `listing_verdict.py`), then `builder/gate.py SLUG`.

**Notes:**
- The SZZ attribution is weak when a later fix only adds code: those rows are `add-only`, and need
  reading by hand.
- The H4 test for "the protection never existed" is a text heuristic over the screener records. The
  reader (step 2) confirms it against the code.

## Phase 2 on klavis-vm (2026-10-22)

**Rules (user):**
- Stacking runs on klavis-vm, with the same user and the same `~/cwe-bench` tree.
- Slugs are `stk-…`.
- **A queue of 16:** a finished job is replaced at once.
- **All builds finish before any trial starts.** CPU-starved trials hit the timeout.

**Steps:**

1. **Batch 1:** `out/batch1.txt` and `out/batch1.tsv`, the 30 usable reader designs in score order.
   The low scorers are kept as calibration points.
2. **Prompts:** `python3 -I stacking/build_prepare_stack.py JOB_ID --project-root /home/mara/cwe-bench`
   for each row, giving `build/<slug>/BUILD-PROMPT.md`.
3. **Run** both phases, build then trial, from `~/cwe-bench`:

       nohup python3 -I stacking/stk_queue.py all --slugs-file stacking/out/batch1.txt > stacking/out/queue/nohup.log 2>&1 &

   - `stacking/stk_queue.py trial` refuses to start while any `run_stack_pipeline.sh` is running.
   - Its trial jobs are (slug, model) pairs: `build/trial.py SLUG --models M --no-verdict`.
     `--no-verdict` keeps the sibling `build/queue.json` untouched.
   - Controls run last.
   - Pairs that are already decided are skipped.
4. **Progress:**
   - `python3 -I stacking/stk_queue.py status`: running jobs with minutes, waiting jobs, done jobs.
   - `stacking/out/queue/{build,trial}.log`: one line per start or finish.
   - `build/<slug>/stack_pipeline.log`: one line per step.
5. **Control gate:** a failed control gate never blocks its stacked task (controls are lowest
   priority).
