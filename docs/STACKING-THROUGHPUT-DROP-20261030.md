# Stacking throughput drop: identification and fix (2026-10-30)

## Finding

Stacked-task yield, counted as both-model breakers that are still kept, out of tasks with a final result:

| Batch | Builder prompt | H3 | H4 | All |
|---|---|---|---|---|
| scale-b1 | build-v1 | 11/32 = 34% | 5/28 = 18% | 16/57 = 28% |
| scale-b2 | build-v1 | 4/24 = 17% | 2/15 = 13% | 6/28 = 21% |
| scale-b7 | build-v1.1 | 1/18 = 6% | 6/42 = 14% | 7/56 = 12% |
| scale-b8 | build-v1.1 | none | 4/60 = 7% | 4/52 = 8% |

The models did not change, and selection did not change in a way that explains the drop:

- **Screener:** DeepSeek for every batch (771 screens, 2026-10-25).
- **Reader:** DeepSeek for 88 of the 99 b1/b2 tasks. The 11 Opus-read tasks yielded 3/11, the DeepSeek-read ones 25/88.
- **Scorer:** `1-select/score_stack.py`, a fixed formula. The score did not predict across batches: b2 had the lowest scores (median 0.17-0.22) and still beat b7 (H4 median 0.55).

## Identification

Codex (gpt-6.1-sol) classified every stacked task of b1/b2 (85) and b7/b8 (107). It read the instruction, manifest, notes, tests and one solving or failing run for each, with the same prompt for both sets. Results are in `~/scratch/tput12` and `~/scratch/tput78c` on klavis-vm.

| | b1/b2 (build-v1) | b7/b8 (build-v1.1) |
|---|---|---|
| Breakers whose held trap the instruction covers only through the general property | 26/28 | 10/11 |
| Solved tasks whose instruction describes or names a found trap | 12/57 = 21% | 27/96 = 28% |
| Solved, primary reason: trap next to the reported route (grep-adjacent) | 11/57 = 19% | 45/96 = 47% |
| Solved, primary reason: instruction leak | 5/57 = 9% | 16/96 = 17% |
| Solved, primary reason: model searched broadly (traps hidden) | 22/57 = 39% | 22/96 = 23% |

**Cause.** Builder prompt build-v1.1 (commit 237aab8c, 2026-10-28, client audit PO-3) added a scope rule. Every trap beyond the advisory had to quote an instruction sentence covering it, and "the general property covers it" counted only when quotable and literal; a trap without such a sentence was dropped.

Builders met the rule in two ways:

- They wrote a sentence per trap, so the instruction describes the trap.
- They kept only the traps that a sentence near the advisory already covered, so the traps sit next to the reported route.

Both make the hidden route findable. This is the checklist problem that addendum v2 (2026-10-24) had already fixed.

**Confidence: medium-high.** The breaker evidence (general-only coverage in 36 of 39 breakers) and the timing fit. b7/b8 also drew on a refill candidate pool, so pool quality is a second, smaller factor that this data cannot separate out.

The sibling/injection drop (b3 12% to b6 4%) is a different cause: those tasks were all built with build-v1.

## Fix (build-v1.2, addendum v4)

**Rolled back:**
1. `common/builder/TASK-BUILD-PROMPT-v1.md`:
   - "Scope of every lever" is now "Reachability of every lever". The quoted-covering-sentence requirement and the manifest `instruction_scope` field are gone.
   - The stop condition "a change outside the scope the report describes" is removed.
   - The prompt states that the general property covers hidden levers, and that no sentence may name or describe one.
2. `common/builder/BUILDER.md` §3l: the "Scope" bullet is replaced by "No per-trap scope sentence".
3. `pipelines/stacking/2-prepare/STACKING-BUILD-ADDENDUM.md` rule 14 and the manifest field list: reachability only.
4. `common/gate/gate.py` `scope_warnings`: warns on a missing `entry_point` only.

**Clarified, so reviewers do not undo the fix by labelling general-only traps unfair:**
- `common/fairness/FAIRNESS-REVIEW-BRIEF.md` step 4a;
- `pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md` S8;
- the auditor brief in `common/audit/postmortem.py`.

All three now say that the general property counts: a hidden route needs no sentence that names or describes it, and `out-of-scope` applies only when no sentence, read literally, covers it.

**Kept from PO-3:**
- reachability and dead paths;
- the conflict check in both directions (builder, fairness, audit);
- the upstream-fix WARN check;
- the other-reading check in repairs;
- notes hygiene (`notes.md` build facts only, `history/`, `notes_filter.py`);
- the delivery refusals.

## Scope of effect

- **Affected:** builds prepared after this release, starting with scale-b11 (staged, no BUILD-PROMPTs yet).
- **Not affected:** the 43 tasks already built with build-v1.1 (b9: 8, b10: 33) keep their instructions.
- **Listing check:** `pipelines/stacking/4-listing` is enforced (`LISTING_ENFORCE` present) but allows one described trap per task. Tightening it is a separate decision.

## Next check

Compare b11 against b7/b8 with the same codex classification once b11 has settled. Expected: the grep-adjacent and leak shares fall back toward the b1/b2 level.
