# Precision validation — plan

Status: **planning only** (2026-10-22). Nothing has run on the VM; nothing in the original pipeline
was written. Every input is a copy (see PROVENANCE.md).

## Question

Can a pre-build screener raise the breaker rate per build from ~25% to ~40%, so that 100 breakers
need ~240 builds instead of ~450? And do post-build features predict breakers before any trial is
spent?

**What the 2026-10-22 analysis claimed** (48 DeepSeek-lane candidates, 12 first-build breakers):
- pre-build: keeping the top 40% by the rule gave 42% precision (8 of 12 breakers kept), tested
  leave-one-out;
- post-build: AUC ~0.76 for sites covered, traps and instruction length. That is a ranking strength,
  **not a 70% precision**. Single cuts give 50–62% precision **in-sample only** (sites ≥ 9: 9/17;
  instruction ≥ 500 words: 8/13), which is optimistic and is exactly what this experiment must test.

## What is already done (in this folder)

| Step | File | State |
|---|---|---|
| Inputs copied with hashes | `inputs/`, `PROVENANCE*.md` | done |
| Training labels (50 candidates; 12 breakers; typo3, hermes-agent ambiguous) | `results/train_labels.csv` | done |
| Leave-one-out check reproduced | `screener/screen.py loo` | 42% at top 40% |
| **Rule frozen** (fitted on all 48) | `results/rule.json`, `results/rule.sha256` (`5947afcc…`) | done; do not refit before the analysis |
| Unseen 100 scored | `results/predictions.csv` | 21 above the bar (score ≥ 3.8) |
| Stacking overlap | `results/eligible.csv` | 9 pool entries share an advisory with the stacking batch (7 H4 entries, plus nuclei and fabio as H3 follow-up advisories). The 7 H4 entries (all below the bar) are left out of the control draw; nuclei (arm A) and fabio (arm B) stay in, since a sibling build is a different task. **93 eligible: 21 above, 72 below** |
| Arms drawn | `results/arm_A_above_bar.csv` (21), `results/arm_B_control.csv` (40), `results/arms.sha256` | fixed seed 20261022 for the control draw; build order shuffled within each arm |
| Stacking batch scored | `results/stacking_scores.csv`; `results/predictions_stacking21.csv` | 7 H4 + nuclei + fabio scored from the pool; the other 21 screened (21/21 records, lessons-v1, Opus 5.5) and scored: **group C = 2** (openbao 17039, gitea 18845; both 3.83, just over the 3.8 bar) |
| Build root, frozen | `root/` (builder, harness, pipeline/evidence.py, sourcer/build_prepare.py, screener_records) | self-contained project root for the builder; experiment files (arms, scores, labels) stay OUTSIDE it, so the builder cannot see its arm |
| Build specs + prompts | `root/build/pv-*/`, `results/build_slugs.csv`, `results/prompt_checks.csv` | 63 (A 21, B 40, C 2); all pass integrity checks (slots filled, surface rule, list-every-sibling step, root path) and contain no arm/score marker |
| Post-build checker + analysis | `screener/postbuild.py` (rule frozen), `screener/analyze.py` | tested on scratch copies: reproduces yamcs-ds's training features exactly; analysis runs end to end on synthetic outcomes |
| Pre-registration | `PREREGISTRATION.md` | locked 2026-10-22T22:18:57Z with hashes of every fixed item |

The bar is absolute: the score at the training set's top-40% cut. The unseen 100 hold fewer
authorization candidates than the first 50 (25 of 100 vs 15 of 50), so only 21 clear it.

## Options considered

**A. Score the remaining 100 (recommended).** Same pool, same feature records, written by the same
screener run before any outcome existed; none was ever trialed. A clean out-of-sample test with
zero screening cost.

**B. Run the screener from scratch.** Tests something else: whether a new screener run reproduces
the features. It adds a second source of variance to the experiment. Do it as phase 2, when scaling,
because the production pool has to be screened anyway: the eligible 93 contain only 21 above-bar
candidates, far short of ~240 builds.

## Top 50 or a bar?

Use the **frozen bar**, not a top-50 cut. A top-50 cut would reach rank 50 of 93, deep below the
bar, and mix the two groups we are trying to compare.

A **concurrent control below the bar** is needed. Without it, a good or bad result could come from
something else that changed since the first 50 (builder prompt, instruction rules, trial setup)
rather than from the screener. Power (simulated, one-sided Fisher test at 0.10):

| Design | Builds | Power if true 42% vs 14% | Power if true 35% vs 20% |
|---|---|---|---|
| 21 above + 21 random below | 42 | 69% | 32% |
| **21 above + 40 random below** | **61** | **80%** | 39% |
| 21 above + all 72 below | 93 | 86% | 46% |

Recommendation: **all 21 above + 40 drawn at random (fixed seed) from the 72 below.** Builds below
the bar are not wasted: a breaker there still counts toward the 100 (expected ~14%, so ~5–6).

## Stacking candidates (Mara, 2026-10-22)

The stacking **trials are ignored** here: a stacked task is a different build, so its outcome does not
test this score. The stacking batch is used only as **more candidates** for our pipeline:

- 7 H4 items are pool entries, all below the bar: not built here.
- nuclei and fabio are pool entries already in arms A and B.
- The other 21 (pattern H3, follow-up advisory `b`) are being screened with the pool's own screener:
  `screener_v2/run_screener.py`, a copy of `stacking/run_screener.py` changed only in paths, lessons
  version and model. It uses the **2026-10-16 prompt + lessons-v1 + claude-opus-5-5**, the exact setup
  that wrote the 150 pool records, so the frozen rule applies unchanged. Records go to
  `results/screener_v2/`, then `screener_v2/make_pool.py` (a copy of the VM converter) gives
  `results/pool_stacking21.jsonl`, then `screener/screen.py score-stacking`.
- Those above the bar form **group C**, built with our sibling pipeline and reported separately. It is
  not part of the A-vs-B test: its candidates were chosen by the stacking score, and 14 of the 21 are
  older than the sourcer's recency window, which raises recall risk.

## Pre-registered success criteria (fixed before any build)

**Builder versions behind the training labels (corrected 2026-10-22, Mara).** The 50 went through
the pipeline several times: run 1 built them (no surface rule); run 2 upgraded the built tasks in place
(`run_upgrade.sh`: instruction rewritten to one general property under BETTER-PATTERNS, at least one
how-type lever); runs 3-4 were hardening (excluded). The 10-21 labels therefore mix two versions:

| Label from | Tasks (usable) | Breakers | Frozen rule: above / below the bar |
|---|---|---|---|
| run 2, upgraded with the surface rule (v2-v4) | 35 | 7 (20%) | 6/15 vs 1/20 |
| run 1 as built (13 recovered late, never upgraded) | 13 | 5 (38%) | 4/4 vs 1/9 |

The authorization signal holds in both (upgraded: authz 4/12, path 0/6, other 3/17). Those bar
splits are partly in-sample. Leave-one-out inside the upgraded 35 alone gives 29% vs a 20% base
(7 positives), a weak lift. Both arms here are built from scratch with the latest builder, which
matches neither training version, so the test is **arm A against arm B under the same builder**:

- **Primary:** A's breaker rate > B's, one-sided Fisher p < 0.10, and at least 10 points higher.
- **Validated:** primary met, and A ≥ 1.5× B.
- **Partial:** A > B by less than that. Keep the score as a soft prior; refit on all rows.
- **Not validated:** A ≤ B. Do not build the pipeline around the score.
- The old 25% stays as context only: if A reaches ≥ 9/21, the screener plus the new builder already
  gives the yield we want, whatever B shows.

Yield denominator = every candidate sent to build (a failed or unsound build counts as not a
breaker). Also reported per sound task. Secondary: AUC of the frozen score over all built candidates.

**Post-build checkpoint (second claim).** After every gate and **before any trial**, record sites
covered, traps, wrong-fix patches, test counts and instruction length into `results/postbuild.csv`.
Freeze a post-build prediction (sites ≥ 9, instruction ≥ 500 words) with its hash, then trial. This
tests the post-build claim on the same builds at no extra cost.

## Trial protocol (identical for both arms)

**Order (Mara):** arm A (21 above the bar) is built and trialed first, as its own batch, because it
should give the most breakers. Arm B (40 control) follows. Both arms use one frozen builder and trial
configuration, so the gap in time does not change the treatment. The arm lists and seed are on record.


1. **Blind arms.** The builder never sees the score or the arm. Build order is shuffled with a fixed
   seed. Slugs get a `pv-` prefix (no clash with `-ds`, `-mm`, `stk-`).
2. **Same settings throughout.** One builder version and one trial configuration for the whole
   experiment, frozen and copied into `pipeline_copy/` before the first build.
3. **Build phase**, then **trial phase**: the same build-then-trial rule as stacking, no mixing.
4. **Trials:** DeepSeek V4.1 Flash first, then MiMo-V2.6-Pro; offline (model API only); early abort
   at the first solve; a breaker = both models fail 3/3. The time cap is the one the first 50 actually
   ran with (2 h), stated in the metadata.
5. **After 3/3 fails on both models:** fairness, then fairfix + re-trial if needed (as for the first
   50); **no hardening** (dropped 2026-10-22); Opus post-run audit. Verdicts only from
   `audit_results.py`.

## Copies still to make (at execution time, from the live VM, read-only)

The snapshot is from 10-21; the live VM may have fixes since. Before the first build, copy into
`pipeline_copy/` with hashes: builder prompts (BUILD / SELFDESIGN-PLAN / BETTER-PATTERNS rules),
`prepare_lane.py`, `run_pipeline.sh`, `gate.py` and `gate_one_ds.sh`, the trial harness and
`trial.py`, fairness/fairfix runners, `postmortem.py`, `audit_results.py`. Each runs from the copy,
with outputs under `precision_validation/`.

## Rough time (on klavis-vm, shared with stacking)

61 builds at a median of ~90 min, 16 slots → ~4 waves, ~6–8 h. Trials: most tasks stop after 1–2
runs; candidates that keep failing take up to 6 runs × 2 h. ~12–18 h. Total about 1–1.5 days,
depending on how the slots are shared with the stacking queue.

## Decisions (Mara, 2026-10-22)

- Option A (score the remaining 100); frozen bar; control of 40; arms kept separate, A first.
- Screen the stacking H3 items (running); stacking trials not counted.

## Still open

1. ~~Builder version~~ **Decided (Mara):** the latest sibling builder, which is local (newer than the
   10-21 VM copy). Frozen in `pipeline_copy/` with hashes and a diff against the VM snapshot. At VM
   time, the VM gets these files rather than its own copies.
2. **VM setup** (next discussion). Proposal: copy this folder to `~/cwe-bench/precision_validation/`
   and use `root/` as PROJECT_ROOT (the prompts already say `/home/mara/cwe-bench/precision_validation/root`;
   regenerate with `prepare_builds.py --project-root ...` if it changes). Tasks and builds then live under
   `root/`, never in the shared `tasks/` or `build/`. Still to copy from the live VM: run_build.sh, drive.sh,
   gate_one_ds.sh / run_pipeline.sh, the trial harness and trial.py, fairness/fairfix runners,
   postmortem.py, audit_results.py, and a check that the live Dockerfile snippet matches the frozen one.
   Slot sharing with the stacking queue: no build beside a trial in either pipeline.
