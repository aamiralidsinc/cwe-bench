# Pattern comparison: do the main batches share the diversity experiment's design weaknesses? (2026-10-29)

**Internal only.** Never copy to the client repo.

**Question.** The chunk-1 diversity audit (`reports/DIVERSITY-CHUNK1-AUDIT-20261028.md`) blamed three builder-design
patterns for its 43 solved tasks:
- (a) injected siblings copy the advisory's sink idiom, so one search finds every site;
- (b) one shared layer covers every site;
- (c) the instruction names the traps.

Do batches 3-6 of the main pipeline have the same patterns? Or did they come from changes made only for the
experiment?

## Bottom line

1. **Chunk 1 did not use a changed builder prompt.** All 66 chunk-1 builds got `build-v1`, the same template as
   batches 5-6. With paths normalised, the A+B, A and B prompts are byte-identical, and so is the self-design plan
   block. `TASK-BUILD-PROMPT-div2` was written on 2026-10-28 *in response to* the chunk-1 audit. It was used only
   for the 6-task div2 pilot on klavis-vm2. The owner's premise is backwards for chunk 1: the patterns cannot come
   from div2.
2. **All three patterns are present in batches 3, 5 and 6 at the same rate as in chunk 1.** We measured them with
   the same blind method on all four groups. In 2 of the checks, batches 5-6 come out a little *worse*.
3. **Cause:** something chunk 1 shares with the main sibling recipe: the `build-v1` sibling brief. It has no idiom
   rule, no one-guard rule, and no listing check on the instruction. The stacking brief (batch 1) adds a one-bug
   test and a listing check. On (c), batch 1 is far cleaner: 23% listing fails, against 91-94% for the sibling
   batches.
4. **These patterns do not separate breakers from solves *within* the sibling batches.** The sibling breakers
   (kuma, medplum, nono, browsershot) show them too. They are a property of how the sibling builder writes every
   task. They are not a sufficient explanation of any one solve.

## 1. Prompt and brief: what each group actually got

Evidence: the rendered `build/<slug>/BUILD-PROMPT.md` of every task (VM, and the chunk-1 bundle
`diversity_population/out/audits/2026-10-28-chunk1/evidence/*/build/*/root/build/*/BUILD-PROMPT.md`). For each
prompt we cut the per-task Inputs section and the paths, then hashed the rest
(`pattern-comparison/prompt_hashes.tsv`, script `scripts/groups.py`).

| Group | Built (UTC) | Template | Distinct static prompts | Same as batches 5-6? |
|---|---|---|---|---|
| Chunk 1 (diversity) | 10-28 05:15-09:09 | build-v1 | 3 (one each for A+B, A, B) | **identical** apart from one path (`/tmp/divq/root/...` in place of the VM root) |
| Batch 5 | 10-28 00:15-13:21 | build-v1 | 3 | reference |
| Batch 6 | 10-28 13:28-20:53 | build-v1 | 3 (same hashes as batch 5) | yes |
| Batch 3 | 10-27 03:20-22:02 | build-v1, earlier revision | 3 | no: lacks the test-quality block added in 57a68cbf (10-27 16:05 EDT) |
| Batch 4 (older builds) | 10-19 to 10-28 | build-v1, older revisions | 6 | no: older paths plus the same missing block |
| Batch 1 (stacking) | 10-25 22:54 to 10-26 02:27 | build-v1 + stacking addendum | one per task | no: adds "Stacked task: additional rules" 1-13 |
| div2 pilot (6 tasks, klavis-vm2) | 10-28, after the audit | build-div2 | n/a | no: adds the audit's fixes |

Normalised prompts: `pattern-comparison/prompt-b5b6-chunk1-AplusB-normalised.md` and
`prompt-b3-AplusB-normalised.md`.

**Differences that could plausibly change difficulty:**

| # | Difference | Who has it | Affects (a)/(b)/(c)? |
|---|---|---|---|
| 1 | **Screener model and prompt.** Chunk 1: Opus 5.5 plus the per-pattern "where sibling sites usually are" hint (`copied/screener/SCREENER-PROMPT-v2.md`). Batches 3, 5, 6: DeepSeek Flash, screener-v2, no hint. Batch 4: Opus, no hint. | chunk 1 only | Indirectly. The hint text reached 0 of 66 build prompts; it only shapes the routes the screener lists. Chunk 1 listed a median of 3 uncovered routes, batches 5-6 a median of 2. |
| 2 | **Source pool and pattern mix.** Chunk 1: older or unreviewed advisories (D1/D2), 22 non-A01 patterns, repos over 1.5 GB excluded. Main: in-window reviewed OSV advisories, picked by score. | chunk 1 only | No direct effect on the three patterns (rates below are equal). It may affect yield (see the funnel report). |
| 3 | **Test-quality block** (refusal helper, stand-ins, no timing flakiness, pristine project tests, score.py, lint). | batches 5-6 and chunk 1; missing in batches 3-4 | Test fairness only. |
| 4 | **Stacking addendum.** Rule 1: one guard closing two traps counts as one concept. Rule 4: one miss-check per concept. Rule 7: one-bug test on every report sentence, plus the listing check. Rule 12: recall check against upstream's fix. Rule 13: a control task. | batch 1 only | (b) and (c). |
| 5 | **div2 changes.** One-search test, one-guard test with `chokepoint.patch`, idiom rule for injected siblings, removal of project tests that assert a removed guard, enumeration ban, `search_terms`/`chokepoint` manifest fields, listing review. | div2 pilot only | (a), (b), (c). Never used in chunk 1 or in any main batch. |
| 6 | **Trial machine.** GitHub runners, plus the `keep_or_release` crash. | chunk 1 only | No. It hid fails and did not make tasks easier. Main runs record fails: 114 of 273 graded runs in batches 5-6 scored below 1.0. |
| 7 | **Gate static-stage race** (blind patch not yet recorded). | both | No: it loses builds. The main pipeline has it too: omnigent-s2 (batch 6) failed the gate with exactly this message. |

## 2. Checks and counts

**Method.** We wrote one review brief (`pattern-comparison/REVIEW-BRIEF.md`) and applied it to every task with a
decided outcome:

| Group | Tasks reviewed |
|---|---|
| Chunk 1 | 53 |
| Batches 5-6 | 94 |
| Batch 3 | 54 |
| Batch 1 | 60 |
| **Total** | **261** |

Twenty Opus reviewers each got about 13 anonymised packets (IDs T001-T307, slugs and the `diversity-` prefix
removed, groups shuffled). They did not see outcomes or transcripts. Each packet held `instruction.md`, the
manifest traps, `injection.patch`, `fix.patch`, the advisory sites and the security tests. The answers:

- `reviews/c*.jsonl`: the raw reviewer output;
- `review_rows.tsv`: the per-task table;
- `packet_key.json`: maps each ID to its task.

Mechanical checks ran on the trial artifacts:

- **Model patches:** `final-code/changed_files.tsv`.
- **Transcripts:** `agent/claude-code.txt`, scanned by `scripts/grepscan.py`. The scan looks at grep and rg
  outputs that list 40 files or fewer, and asks whether one such output listed every trap file in the manifest.
  Results: `grepscan.tsv` (main) and `grepscan_div.tsv` (chunk 1).

**Outcome classes:**
- **solved by both:** S_both.
- **one model:** S_ds_only or S_mimo_only.
- **breaker:** B_delivered or B_kept.
- **dropped:** B_dropped or B_withdrawn.
- **Chunk 1:** the corrected outcomes in `diversity_population/out/regrade-chunk1/OUTCOMES.md`. openemr and seanime
  are breakers. laravel-mongodb, databasement, mingo and open-web-analytics are one-model. The other 47 were solved
  by both.

### (a) Idiom copy: one search finds the sites

| Check | Chunk 1 | Batches 5-6 | Batch 3 | Batch 1 (stacking) |
|---|---|---|---|---|
| Task has at least one injected sibling that uses the advisory's own call, name or key | 44/53 (83%) | 80/94 (85%) | 48/54 (89%) | 6/60 (10%; most stacking tasks have no injection) |
| Injected hidden traps that an advisory search term hits | 62/94 (66%) | 127/182 (70%) | 89/120 (74%) | 8/12 |
| `one_search` ALL or MOST (one or two advisory terms hit every hidden trap) | 22/53 (42%) | 59/94 (63%) | 30/54 (56%) | 31/60 (52%) |
| **Transcripts:** solved runs where one search output listed every trap file | 42/85 (49%) | 84/150 (56%) | 28/69 (41%) | 16/51 (31%) |
| Tool call at which that search came (median) | 11.5 | 7 | 11.5 | 9.5 |

The same checks, split by outcome:

| `one_search` ALL or MOST | Solved by both | One model | Breaker |
|---|---|---|---|
| Chunk 1 | 19/47 | 2/4 | 1/2 |
| Batches 5-6 | 34/56 | 23/36 | 2/2 |
| Batch 3 | 22/34 | 4/11 | 3/6 |
| Batch 1 | 13/26 | 9/12 | 7/17 |

**Calibration.** Our blind `one_search` label is stricter than the chunk-1 audit's `sites_idiom` label, which had
the transcripts. Of the 23 tasks the audit called "same-idiom", we marked 9 ALL or MOST, 12 SOME and 2 NONE. So the
absolute rates understate the pattern; the group comparison uses one method throughout.

### (b) One shared layer covers every site

| Check | Chunk 1 | Batches 5-6 | Batch 3 | Batch 1 |
|---|---|---|---|---|
| Reviewer: a fix at the single most-shared layer passes every security test (`one_guard` YES) | 6/53 (11%) | 13/94 (14%) | 4/54 (7%) | 10/60 (17%) |
| **Patches:** solved runs whose fix touched fewer non-test files than the task has distinct trap files (DeepSeek + MiMo) | 12/87 (14%) | 29/149 (19%) | 26/67 (39%) | 14/47 (30%) |
| Solved runs touching at most 1 non-test file | 4/89 | 15/157 | 5/75 | 5/55 |

By outcome, `one_guard` YES:

| Group | Solved by both | One model | Breaker |
|---|---|---|---|
| Chunk 1 | 6/47 | 0/4 | 0/2 |
| Batches 5-6 | 7/56 | 6/36 | 0/2 |
| Batch 3 | 3/34 | 0/11 | 1/6 |
| Batch 1 | 5/26 | 2/12 | 1/17 |

**Calibration.** The blind one-guard judgment is weak. Of the 11 tasks the audit blamed primarily on a shared layer,
our reviewers said YES on only 2. They cannot run code and judged from patches. The patch-breadth check is the
better one. It shows chokepoint-style solves at least as often in the main batches as in chunk 1.

### (c) The instruction names or describes the traps

We used the stacking listing check v3 rubric verbatim. A task FAILs when any hidden trap is NAMED, or more than one
is DESCRIBED. The advisory route is exempt: by `origin` where the manifest has it, otherwise by the reviewer. Most
sibling manifests have no `origin`: 52 of 53 in chunk 1 and 76 of 94 in batches 5-6.

| Check | Chunk 1 | Batches 5-6 | Batch 3 | Batch 1 |
|---|---|---|---|---|
| Listing FAIL | 50/53 (94%) | 86/94 (91%) | 51/54 (94%) | 14/60 (23%) |
| Any hidden trap NAMED | 22/53 (42%) | 26/94 (28%) | 12/54 (22%) | 4/60 (7%) |
| Hidden traps NAMED or DESCRIBED | 181/224 (81%) | 322/393 (82%) | 226/278 (81%) | 52/190 (27%) |
| Specificity, 1-5 (mean) | 2.85 | 2.87 | 2.85 | 1.92 |
| Specificity 4 or more | 10/53 | 13/94 | 9/54 | 1/60 |

By outcome, listing FAIL:

| Group | Solved by both | One model | Breaker |
|---|---|---|---|
| Chunk 1 | 45/47 | 3/4 | 2/2 |
| Batches 5-6 | 52/56 | 32/36 | 2/2 |
| Batch 3 | 32/34 | 10/11 | 6/6 |
| Batch 1 | 5/26 | 3/12 | 5/17 |

**Calibration.** On batch 1, our reviewers matched the pipeline's own listing check (`build/<slug>/listing.json`)
on 46 of 57 tasks. They were stricter on 10 and more lenient on 1. Even allowing for that, the gap between 23% and
91-94% is far too large to be a reviewer effect.

### Other causes the chunk-1 audit named

| Cause | Main batches 5-6 | Shared with the main prompt? |
|---|---|---|
| Harness crash hid fails (`keep_or_release`) | No: 114 of 273 graded runs below 1.0 are recorded | Actions only |
| Gate race lost builds | Yes: omnigent-s2 (1 of the 5 gate fails in batches 5-6) | Yes: `common/gate/gate.py` (the div copy fixed it; main did not) |
| Project test still asserts a removed guard (lxd) | Not measured (needs the repo tree) | Yes: build-v1 has no rule; div2 added one |
| Tests too weak | Not the cause in the audit (42 of 43 strong); not re-measured | n/a |
| Fast and solved early | DeepSeek first-attempt solve rate 80% (75/94), chunk 1 79% (41/52); median minutes of solved runs: DeepSeek 16 against 17, MiMo 66 against 84 | n/a |
| Screener per-pattern hint | Absent | Diversity only |

### Deeper reading: the 22-task sample (`~/scratch/yield-audit/sample.tsv`)

In the table, "inj hit" means injected sites hit by an advisory search term. N/D/H means hidden traps named,
described, and the total hidden.

| Task | Batch | Outcome | one_search (inj hit) | one_guard | Listing (N/D/H) | Spec | Solved runs where one search listed all trap files |
|---|---|---|---|---|---|---|---|
| phpsysinfo-s2 | b6 | both solved | SOME 1/2 | NO | FAIL 0/3/3 | 3 | 0/2 |
| wakaru-s2 | b5 | both solved | ALL 2/2 | NO | FAIL 2/2/4 | 3 | 0/2 |
| ts-stack-s2 | b5 | both solved | ALL 1/1 | YES | FAIL 2/2/4 | 4 | 2/2 |
| hydro-s2 | b6 | both solved | SOME 1/3 | NO | FAIL 0/4/4 | 3 | 1/2 |
| process-compose-s2 | b6 | both solved | NONE 0/1 | NO | FAIL 0/2/2 | 4 | 0/2 |
| claw-orchestrator-s2 | b5 | both solved | SOME 2/2 | NO | FAIL 1/3/4 | 3 | 0/2 |
| n8n-node-sqlite3-s2 | b5 | both solved | SOME 0/2 | NO | FAIL 0/2/4 | 2 | 0/2 |
| praisonai-s2 | b6 | both solved | SOME 1/2 | NO | FAIL 0/2/4 | 2 | 1/2 |
| piscina-s2 | b6 | both solved | SOME 1/2 | NO | FAIL 0/4/6 | 3 | n/a |
| middleware-s2 | b5 | both solved | MOST 2/2 | NO | FAIL 1/4/5 | 4 | 1/2 |
| hurl-s2 | b6 | DS only | MOST 2/2 | YES | FAIL 1/0/4 | 2 | 2/2 |
| mcp-context-forge-s2 | b5 | DS only | MOST 1/2 | NO | FAIL 0/2/2 | 2 | 2/2 |
| pi-s2 | b5 | DS only | SOME 0/1 | NO | FAIL 0/4/5 | 3 | 0/2 |
| infracost-s2 | b5 | DS only | SOME 2/2 | NO | FAIL 0/5/5 | 2 | 1/1 |
| kuma-s2 | b5 | breaker | MOST 2/2 | NO | FAIL 2/5/7 | 3 | n/a |
| medplum-s2 | b6 | breaker | MOST 3/3 | NO | FAIL 0/5/5 | 4 | n/a |
| nono-s2 | b3 | breaker | MOST 2/2 | NO | FAIL 0/4/4 | 3 | n/a |
| browsershot-s3 | b3 | breaker | SOME 0/2 | NO | FAIL 0/3/5 | 2 | n/a |
| spark-s3 | b3 | both solved | SOME 1/3 | YES | FAIL 0/5/6 | 3 | 0/2 |
| tilt-s2 | b3 | both solved | SOME 2/2 | UNSURE | FAIL 2/5/7 | 4 | 0/3 |
| stk-liferay-portal-ghsa3qq5 | b1 | breaker | NONE | NO | FAIL 0/2/2 | 2 | n/a |
| stk-commonmark-ghsajjv6 | b1 | breaker | NONE | NO | PASS 0/0/3 | 1 | n/a |

Every sibling task in the sample fails the listing check, breakers included. kuma-s2 is a breaker even though
`InsecureSkipVerify` finds both of its injected siblings: its depth comes from a coupled system-trust value and a
producer off the check's path. The two stacking breakers have all-real routes that no search for the check finds.

## 3. Verdict per pattern

| Pattern | In batches 3-6? | Rate against chunk 1 | Cause |
|---|---|---|---|
| (a) Idiom copy / one search | **Present** | Same or higher: 85% of tasks have an idiom-copy sibling (chunk 1: 83%); one search listed every trap file in 56% of solved runs (chunk 1: 49%) | Shared `build-v1`: injected-sibling rule 6 has no idiom requirement, and it calls where-type levers "extras" without forbidding them. Not a diversity change. |
| (b) One shared layer | **Present** | Same: reviewer 14% against 11%; narrow solves 19% against 14% (batch 3: 39%) | Shared `build-v1`: no one-guard test and no chokepoint check. Only the stacking addendum's rule 1 addresses it, and batch 1 is not lower on these checks. |
| (c) Instruction names traps | **Present** | Same: 91% listing FAIL against 94%; 82% of hidden traps named or described against 81% | Shared `build-v1` sibling brief: "never by a sentence of its own" is stated but never checked. The listing check runs only for stacking, where the rate is 23%. |

None of the three comes from div2 or from the diversity changes. The diversity-only differences are the screener
hint, the source pool and the Actions harness. They may explain part of chunk 1's lower yield. They do not explain
the three patterns, which the main sibling batches show at the same rate.

**Limits:**
- The patterns are almost universal in sibling tasks, breakers included. So this audit shows that they are shared.
  It does not show that removing them restores yield.
- In the div2 pilot, builds that passed the one-search and one-guard tests were still solved, 5 of 6, while their
  instructions still described the traps (`DIVERSITY-CHUNK1-FUNNEL-20261029.md`). The yield drop from 17% (batch 3)
  to about 2% (batches 5-6) is not explained by these patterns either: batch 3 has them at the same rate.

## 4. What to change in the main builder, and which diversity items apply

**Builder prompt (`common/builder/TASK-BUILD-PROMPT-v1.md`, sibling track):**
1. **Apply the stacking report rules to sibling builds.** Port rule 7 (the one-bug test on every report sentence)
   into the sibling brief. Run `pipelines/stacking/4-listing/run_listing_check.sh` after the gate. This is the only
   pattern where we have a working contrast: 23% FAIL with the rule, 91-94% without it.
2. **Make sibling manifests carry trap `origin`.** Most sibling manifests have none, so the advisory route cannot be
   exempted mechanically (76 of 94 in batches 5-6 lack it).
3. **Port the div2 Design additions as written:** the one-search test (`manifest.search_terms`), the idiom rule for
   injected siblings, the one-guard test with `checks/chokepoint.patch` expected to fail security, and the removal
   of project tests that assert a removed guard.
4. **Port the div2 report bans:** arrival-form lists, field or category names, and pre-encoded examples.

**Gate:** add the audit's cheap checks:
- grep the advisory's search terms against the manifest sites;
- run `chokepoint.patch`.

Also fix the static-stage race in `common/gate/gate.py`, as the diversity copy already did (it cost omnigent-s2).

**Diversity remediation items, mapped to the main pipeline:**

| Item | Applies to main? |
|---|---|
| Builder 1-4 (idiom, route around the shared layer, goal-only report, delete stale project tests) | Yes, all four |
| Gate grep check and chokepoint check | Yes |
| Gate race fix | Yes |
| Instruction rewrite after the listing review | Yes, for sibling builds |
| Prefer the stacking recipe (funnel report) | Yes: it is already ours, and has the higher yield |
| Selection: several sink APIs for one effect; per-route checks with no shared middleware | Yes, as screener preferences |
| `keep_or_release` fix | No: Actions only |
| Drop or test the screener's per-pattern hint | No: diversity only |
| Lift the 1.5 GB repo limit | No: diversity only |
| Per-pattern quotas | No: separate experiment |

**Expectation:** these changes remove shared weaknesses. They are not proven to raise yield on their own. Test them
on one sibling batch against the current prompt before rebuilding at scale.

## Evidence

The folder `reports/yield-audit-20261029/pattern-comparison/` holds:
- `prompt_hashes.tsv`, `inputs.tsv`: prompt identity and screener metadata per task;
- `REVIEW-BRIEF.md`, `reviews/c00-c19.jsonl`, `packet_key.json`, `review_rows.tsv`: the blind design review;
- `grepscan.tsv`, `grepscan_div.tsv`, `trapfiles.json`: the transcript one-search scan;
- `scripts/`: the analysis scripts. They ran from the session scratchpad and use relative paths.

Inputs on klavis-vm, all read only (the only writes were under `~/scratch/yield-audit/pc/`):
- `~/cwe-bench/build/<slug>/` and `~/cwe-bench/tasks/<slug>/`;
- `~/.tb-graders/cwe/jobs/*/final-code/` and `agent/claude-code.txt`.
