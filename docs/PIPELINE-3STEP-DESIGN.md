# Three-step pipeline design (scale run)

**Status:** built 2026-10-25 (section 7); runbook in `pipelines/router/README.md`. Dry run: see section 9.

## 1. The idea in one paragraph

Every candidate advisory gets one chance at the strongest recipe first. **Step 1 (stacking)** screens the whole
pool and builds stacked tasks from the candidates it selects. **Step 2 (sibling injection)** builds from the
candidates stacking did **not** select. **Step 3 (sibling injection again)** takes the candidates stacking selected
whose stacked task **was solved**, and builds a sibling-injection task from them. Nothing is built twice by the same
recipe, and nothing stacking rejects is wasted.

## 2. Flow

```
OSV index (sourcer/index/candidates.sqlite)
  └─ SCREEN once: common/screener (one prompt, shared by both pipelines)        → out/screener/<entry>.json
       ├─ STEP 1 stacking selection: H4/H3/SZZ grouping → reader (Opus) → score → stacked selection
       │     build → [parallel checks] → .sound → trial → audit → fairness after 3/3 → breaker
       │                                                   └─ solved (any model) ──┐
       ├─ STEP 2 sibling selection on screened − stacking-selected (by entry id AND repo)
       │     rerank → select → build → [parallel checks] → .sound → trial → ... → breaker
       └─ STEP 3 sibling on stacking-selected whose stacked task was solved  ◄────┘
             primary (reported) advisory of the stacked task → sibling build → [parallel checks] → trial → ...
```

[parallel checks] = after a build, these run **at the same time**, and the task goes to trial only when all pass:
- the static checks and the stacking listing check (hint leakage);
- the Docker gate, with **nop, oracle and every patch check as separate concurrent Harbor jobs** (today they run
  one after another); the task's gate time becomes the slowest single job instead of the sum;
- the blind fix (now works on `/workspace` tasks too).
On SOUND the gate writes `gate_fingerprint.json` (section 5).

The three steps run **as streams, not one after another**: step 2 starts as soon as stacking selection is done (it
only needs the "not selected" list); step 3 picks up each stacked task the moment its trial comes back solved.

## 3. Routing rules (what goes where)

| Rule | Detail |
|---|---|
| One screen | the screener output feeds both selections; step 2 and step 3 do no screening of their own |
| Step 2 exclusion | exclude every candidate stacking selected, by entry id **and** repo (a repo stacked once is not used again in step 2, to avoid near-duplicates) |
| Step 3 trigger | a stacked task that **any** model solved (both solved, or one solved = at best a single-model breaker). Open question for the owner: also route single-model stacked breakers, or keep them as they are? Default: route them |
| Step 3 input | the stacked task's primary (reported) advisory, its clone and screen record; the sibling builder injects siblings into the same repo |
| No duplicates | an advisory already built by the sibling recipe (any batch) is not built again; checked against `pipelines/sibling/out/vm_used.json` and the build dirs |
| Controls | stacking `-control` twins are **not gated or trialled** in the scale run (no time; owner decision 2026-10-25). The builder may still write them |

## 4. Trial, audit, fairness (unchanged rules)

- DeepSeek and MiMo, 3 runs each with early abort on a solve, 3 h limit; a 3 h timeout counts as a fail.
- Audit failing runs only (solves count unaudited).
- Fairness once, after a model fails 3/3; fairfix if NOT_READY; a human question is answered in **one decision
  file the fairness reader reads** (section 7, item 4).
- Delivery with `common/util/export_delivery.py` in the client layout (section 6).

## 5. Re-gate rule (enforced)

Any change to a task's tests, solution, environment or check patches after its gate pass (fairfix, testfix,
upgrade, hand repair) invalidates the gate: re-gate the whole task, then regrade (or rescore a pure removal), then
re-audit changed rewards. `common/gate/fingerprint.py` makes `run_trial.sh` and `regrade.py` refuse a stale task.
Full text: the "Re-gate rule" section of `pipelines/*/GUIDE.md`.

## 6. Delivery layout (client request, 2026-10-25)

```
/tasks/<task_name>/
/trajectory/<task_name>/<model_name>/rollout<N>/reward.json        (required)
                                             /trajectory.json    (required, ATIF-v1.7: Harbor's agent/trajectory.json)
                                             /verifier/          (optional, verifier logs)
```
`python3 common/util/export_delivery.py <out> <slug>... [--name slug=delivered-name]` writes it from the runs the
ledger counts, checks each trajectory with Harbor's validator, and lists skipped runs. Tested 2026-10-25 on
stk-filebrowser and mockoon-ds (13 rollouts, all valid). The precision_validation runs have no trajectory (GitHub
Actions kept none), so those tasks need VM runs before they can be delivered this way.

## 7. Launch items (built 2026-10-25)

| # | Item | Where |
|---|---|---|
| 1 | Router: stacking batch, step-2 pool, step-3 queue | `pipelines/router/route.py`, `README.md`; sibling lane folder overrides `LANE_RECS` / `LANE_PIPE` / `LANE_SUFFIX` |
| 2 | Parallel gate: static, then nop / oracle / patches at the same time, each with its own report and retries; combined `gate_report.json` | `common/gate/gate_one_ds.sh`, `gate.py --report/--patch` |
| 3 | Parallel post-build checks: listing (stacking), gate, blind fix together; then the blind patch check; fingerprint | `common/gate/postbuild.sh`, used by both build chains |
| 4 | Decision file `build/<slug>/HUMAN-DECISION.md`, read by the fairness reader; 13 earlier decisions migrated | `common/fairness/fairness_verdict.py` |
| 5 | Stacking scale mode: no control gate, no control trials (`STACK_CONTROLS=1` restores) | `run_stack_pipeline.sh`, `stk_queue.py` |
| 6 | Dry run | section 9 |

Also done: blind-fix `/workspace` fix, gate fingerprint + re-gate rule, delivery exporter, DeepSeek screening of
the whole OSV pool (771 repos) and the DeepSeek stacking reader (125 designs).

Open point for the owner: `run_blindfix.sh` gives its agent only the instruction and the code, while
`BLIND-FIX-BRIEF.md` (and the 2026-10-20 rule) says the soundness control is written with everything in view. So a
failing blind patch is treated as a warning (`.blind_fail`), never as unsound.

## 8. Estimate: stacking screens the OSV pool

**Pool:** the first OSV index has **2,531 candidates** (2,511 `candidate` + 20 `shortlisted`); **587** were already
screened or used, so **1,944** are new.

**Measured on batch 1** (`pipelines/stacking/out/`):
- screener (Opus 5.5 via Claude Code, every candidate): median **1.8 min**, p90 2.9 min, about **$0.70** each
  (API-equivalent cost as reported by Claude Code), plus about 0.5 min of clone and prepare per candidate;
- reader (Opus 5.5, only on stacking's shortlist): median **2.5 min**, about **$0.70** each; batch 1 sent about
  half of its screened candidates on to the reader (51 reader jobs from about 100 screened).

| Stage | Items | Parallel 3 (batch 1 setting) | Parallel 10 | Parallel 20 | Cost |
|---|---|---|---|---|---|
| Screen | 1,944 | ≈ 24 h | ≈ 7 h | ≈ 3.5–4 h | ≈ $1,400 |
| Reader (≈ half) | ≈ 950 | ≈ 15 h | ≈ 4.5 h | ≈ 2.5 h | ≈ $650 |
| **Stacking selection, total** | | **≈ 39 h** | **≈ 11–12 h** | **≈ 6–7 h** | **≈ $2,000** |

Grouping and scoring between the two stages are scripts and take minutes. The limit on parallelism is the Claude
account's rate limit, not the VM: the agents mostly wait on the model API. **Parallel 10 (about half a day) is the
realistic plan**; try 20 if the account allows it. Step 2 needs no extra screening, because it reuses these
records. The whole pool screened also gives step 2 a ranked pool for the rest of the scale run.

## 9. Dry run

(to be filled with the dry-run result)
