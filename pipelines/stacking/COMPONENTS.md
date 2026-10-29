# Stacking pipeline: component versions

**Rule:** always use the CURRENT file, which is the one at its live path. "Last proven" names the version that
produced the batch-1 results (2026-10-23..25). When the two differ, the current version has fixes that **have not
run yet**, and its first run deserves a closer look.

All old versions are in `pipelines/stacking/archive/versions/`, unless noted. Each file name carries the date it
was replaced, and `archive/README.md` lists every file with its original path, date and sha256.

| Component | CURRENT (live path) | Status | Last proven (batch 1) | Archived versions |
|---|---|---|---|---|
| Screener runner | `common/screener/run_screener.py` + `common/screener/SCREENER-PROMPT-v2.md` (lessons-v2) | proven | same | sibling screener history: `common/archive/old-prompts/` |
| H4 ranking / H3 pairs / SZZ / H1-H2 | `1-select/h4_rank.py`, `h3b_pairs.py`, `szz_pairs.py`, `h12_groups.py` | proven (H1/H2 unused) | same | none |
| Reader | `1-select/run_reader.py` + `STACKING-READER-PROMPT.md` v1 | proven | same | none |
| Scorer | `1-select/score_stack.py` + `stacking_weights.json` v1 + `calibration/` | proven; the planned weight refit is not done | same | none |
| Batch choice | `out/batch1.txt` (by hand) | — | — | — |
| Prompt filler | `2-prepare/build_prepare_stack.py` | proven | same | none |
| Build addendum | `2-prepare/STACKING-BUILD-ADDENDUM.md` "v2" (adds `LISTING_ENFORCE` wording and rule 13: control instruction byte-identical for life) | **never run in a build** | v1-pre (`"expect": "fail"`); it exists only inside `build/stk-*/BUILD-PROMPT.md` | `STACKING-BUILD-ADDENDUM.md.bak-20261024T0900Z` (v1, expect `security_fail`), `.bak-20261024T1809Z` (v2) |
| Driver | `3-build-gate/run_stack_pipeline.sh` (listing step, advisory unless `LISTING_ENFORCE`) | **never run** | `run_stack_pipeline.sh.bak-20261024T0900Z` (no listing step) built all 30 | `.bak-20261024T0900Z`, `.bak-20261024T1809Z` (listing as a hard gate) |
| Post-build normaliser | `3-build-gate/normalize_expect.py` | proven | same | none |
| Static stacking check | `3-build-gate/check_stack.py` (adds rule 13) | proven in the repair chains | `.bak-20261024T1809Z` in the builds | `check_stack.py.bak-20261024T1809Z` |
| Listing reviewer prompt | `4-listing/STACKING-LISTING-CHECK.md` **v3** | proven: calibrated 17/17, lenient 2/63 (`out/calibration-listing/v3/`) | v3 | `.bak-20261024T1809Z` ("v1"), `.bak-v1-20261024` (also labelled "v1", with gating notes), `.bak-v2-20261024` (v2) |
| Listing launcher / verdict | `4-listing/run_listing_check.sh` (tamper guard), `listing_verdict.py` (unknown label = ERROR) | proven | same | `.bak-20261024T1809Z` each |
| Listing calibrator + switch | `4-listing/listing_calibrate.py`, `4-listing/LISTING_ENFORCE` (present = enforced) | proven | same | none |
| Upgrade prompt | `5-upgrade/STACKING-UPGRADE-PROMPT.md` **v2** (rule 3: keep what the fix itself must add) | **never run** | `STACKING-UPGRADE-PROMPT.md.bak-v1-20261024` ran all 24 upgrades and damaged 11 | `.bak-v1-20261024` |
| Upgrade launcher / batch | `5-upgrade/run_upgrade_stack.sh`, `upgrade_stack_batch.sh` | proven | same | none |
| Queue | `6-trial/stk_queue.py` (skips `.listing_fail`) | proven: trial phase, 84 jobs | the build phase used `stk_queue.py.bak-20261024T0900Z` | `.bak-20261024T0900Z` |
| Trial runner | `common/trial/trial.py` → `common/trial/run_trial.sh` | proven | same | `common/archive/versions/` |
| Audit | `common/audit/postmortem.py` + Opus 5.5-high sub-agents; verdicts from `common/audit/audit_results.py` | proven | same | `common/archive/versions/build/` |
| Fairness addendum | `7-fairness/STACKING-FAIRNESS-ADDENDUM.md` (v2 + "edit only the stacked instruction") | proven: every review from 10-24 22:18Z | same | `.bak-20261024T0900Z` (v1, used by the 10-23 batch), `.bak-20261024T1809Z` |
| Fairness launcher | `7-fairness/run_fairness_stack.sh` + `common/fairness/FAIRNESS-REVIEW-BRIEF.md` | proven | same | brief history: `common/archive/versions/builder/` |
| Fairfix | `8-fairfix/run_fairfix_stack.sh` (`FAIRFIX_BRIEF` override; copies to the control; re-runs the listing check; with `REPAIR_INPUTS` set by the queue's `repair` job it runs `pipelines/sibling/10-fairfix/run_repair_agent.sh --stacked` instead, 2026-10-28) | proven: every repair chain (repair mode: not yet run) | same | `.bak-20261024T1809Z`, `.bak-brief-20261024` |
| Docs | this file, `GUIDE.md` | — | — | `archive/README-before-reorg.md` (the old stacking/README.md) |

## One-off scripts (archived, not part of the run order)

- `archive/one-off/`:
  - `regate.sh`, `regate_batch.sh`, `regate_fixed2.sh` (2026-10-23 re-gates);
  - `fairness_batch.sh`;
  - `backup_candidates.sh`;
  - `stacking_restart.sh`, which is **destructive** and is left non-executable.
- `archive/night-chains-20261024/`: the 16 repair chains from the 2026-10-24/25 night. Their pattern is the
  repair loop in GUIDE.md, step 12.
