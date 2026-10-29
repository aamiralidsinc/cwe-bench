# Breaker yield audit (independent), 2026-10-29

Internal report. Not for the client.

Scope: why the both-model breaker yield fell from 37% (batch 1) to about 2% (batches 5-6).
Evidence: the 22-task sample, the batch 1-6 outcome list, the trial ledger, briefs, manifests, selection files
and solver transcripts on klavis-vm. I did not read the diversity reports or notes.
My scripts and their outputs are on the VM in `~/scratch/yield-audit/tools/` and `~/scratch/yield-audit/*.tsv`.

## Short answer

1. **The 2% for batches 5-6 is mostly a snapshot effect.** Solved tasks finish after one run per model. Failing
   tasks need 3 runs per model, so they finish last. At the snapshot, b5 already had 4 tasks that both models
   failed in every graded run (3 still awaiting audit), and b6 had 2 plus 7 more that DeepSeek failed 3/3 while
   MiMo was still running (many MiMo runs cut by rate limits). Expected final yield before audit: b5 about 7-9%,
   b6 about 10-15%.
2. **The real drop is the recipe change, not the batches getting worse inside a recipe.** Batch 1 was all
   stacking. From batch 3 on there is no stacking at all. Stacking yields about twice the sibling recipe, and
   that ratio holds at every selection rank. Inside the sibling recipe the yield is flat with noise: 11%, 20%,
   12%, 7%, ~13% (b2-b6).
3. **Why siblings fall:** the solvers find every trap site in the first minutes. In 190 of 250 sibling tasks,
   DeepSeek's first run opened every trap file within 3 minutes. Siblings share the reported idiom, so the
   first grep returns them, and one shared helper fixes them all. Sibling tasks hold only when a site needs a
   judgement the solver gets wrong (a shape, a wrong object, a "test tool" it decides to leave). Stacked tasks
   hold mostly because the solver never opens the other advisory's code.
4. **Selection scores do not predict outcome inside the sibling pool.** Later batches were drawn from lower
   scores (median 8.6 in b2, 5.0 in b6), but b6 has more DeepSeek fails than b5. Lower scores did not cause
   the drop.
5. The given early-batch yields include breakers that were later dropped or withdrawn as unfair (5 of 22 in b1,
   3 of 9 in b3). Counting only kept/delivered breakers, b1 is 28%, not 37%.

## 1. Are the numbers right?

The given numbers match the outcome file, with three caveats.

| Batch | Recipe | Given yield | Both-fail now (trial ledger) | Kept/delivered only | DS fail (≥3 graded fails, no pass) | DS first-run pass |
|---|---|---|---|---|---|---|
| b1 | 57 stacked + 3 sibling | 37% (22/60) | 22/60 | 17/60 = 28% | 29/60 = 48% | 24/60 = 40% |
| b2 | 36 stacked + 19 sibling | 17% | 10/55 | 8/55 = 15% | 17/55 = 31% | 34/55 = 62% |
| b3 | sibling | 17% (9/54) | 11/54 | 6/54 = 11% | 14/54 = 26% | 34/54 = 63% |
| b4 | sibling (older builds) | 11% | 8/68 | 6/68 = 9% | 11/68 = 16% | 51/68 = 75% |
| b5 | sibling | 2% (1/52) | 4/57 (3 awaiting audit) + 1 pending | 1 + 3 awaiting | 6/57 = 11% | 46/57 = 81% |
| b6 | sibling | 2% (1/42) | 2/53 confirmed + 7 DS-failed with MiMo pending | 1 + 1 awaiting | 10/53 = 19% (+2 pending) | 38/53 = 72% |

Caveat A, censoring (measured). The "finished" denominator leaves out exactly the tasks that are failing.
- b5: `mcp-pinot-s2`, `djust-s2`, `mollieplugin-s2` failed by both models in every graded run, awaiting audit.
  `migration-planner-s2`: DeepSeek 0/3, MiMo 1 fail plus 1 rate-limit cut.
- b6: `core-s2` both-fail, awaiting audit. DeepSeek 0/3 and MiMo not yet passed: `wasmtime-s2`,
  `deepseek-harness-s2`, `crossplane-runtime-s2`, `smarty-s2`, `shescape-s2`, `jupyter-server-s2`,
  `tinyauth-s2`.
- Over all batches, when DeepSeek fails 3/3, MiMo also fails 3/3 in 72% of tasks (57 of 79). b5-b6 so far: 6 of 8.
  Applying 72% gives about 4.7/57 (8%) for b5 and about 7/53 (13%) for b6, before audit.
- Audit has removed about 22% of both-fail tasks in b1-b4 (11 of 49). After audit, expect roughly 6% (b5) and
  10% (b6). That is the same level as b3 (11%) and b4 (9%) after audit.

Caveat B, dropped breakers in the given yields (measured). `B_dropped` and `B_withdrawn` count as breakers in
the given figures: b1 5, b2 1 (+1 kept), b3 3, b4 1. These were false breakers, mostly test artifacts. The brief
added test-quality rules after b3 (refusal helper, stand-ins that mirror real classes, pristine project tests,
crashed runner counts as failure). Fewer false breakers later is a quality gain, but it makes the later
batches look worse against the early figures.

Caveat C, test repairs (measured, small, all batches). Regrades after test repairs turned graded fails into
passes. Tasks whose original grading was all-fail for both models and are now not breakers: b1 2, b2 1, b3 2,
b4 6, b5 3, b6 1. This is spread across batches, so it does not explain the drop.

Also: DeepSeek's fall from 48% to 14% and its first-run rise from 39% to 75% is the recipe change. Split by
recipe, DeepSeek is stable: stacking 45% fail and 46% first-run pass (b1-b2); siblings 20% and 70% (b2-b4),
15% and 76% (b5-b6). By trial date, sibling DeepSeek fail rates were 15-20% on each half-day from 10-27 to
10-29. Solver settings were the same in every batch: same env vars, same model id, same tool list. Claude Code
went from 2.1.310 to 2.1.312 between b1 and b3. I saw no effect, but cannot rule one out.

One labelling oddity: `S_ds_only` in `all-b1-b6.tsv` does not always mean that MiMo failed. `hurl-s2` and
`pi-s2` have MiMo passes in the ledger. Use the ledger for model verdicts.

## 2. Why the sample tasks fell or held

Method: for each task I read the instruction, the manifest traps, the failing tests across all runs, and
DeepSeek's first transcript (and MiMo's where useful). "Opened" means the trap file's name appears in a tool
call (Read, cat, sed, grep path). "Edit" is the first Edit or Write to it. Times are minutes from the start.

| Task | Batch | Outcome | Main reason it fell or held | Evidence |
|---|---|---|---|---|
| phpsysinfo-s2 | b6 | solved both (DS 5 min, MiMo 29) | DS's first grep (`ALLOWED\|X-Forwarded-For\|REMOTE_ADDR`) returned the core and both injected files at 0.0. The `tools/` scripts were read at 1.1 and fixed at 3.7. The coupled "trusted proxy" lever is spelled out in Contracts (`TRUSTED_PROXIES`, its format and meaning). One shared helper fixed all sites. | jobs/phpsysinfo-s2-deepseek-r1-*/…/agent/claude-code.txt; tasks/phpsysinfo-s2/instruction.md |
| wakaru-s2 | b5 | solved both (after regrade) | All 9 trap files opened within 0.5 min, all edited at 4.2-4.6. One path-containment helper covers every writer. | build/wakaru-s2/manifest.json; DS r1 transcript |
| ts-stack-s2 | b5 | solved both (DS 10) | 4 of 5 traps are in one file (`buildSignableTransaction.ts`). The injected sibling sits next to it and is dispatched from the same `createAction`. | manifest traps; DS r1 transcript |
| hydro-s2 | b6 | solved both (DS 19) | 5 session-invalidation sites share one token-model idiom. All opened by 0.8, edited at 5.0-5.6. MiMo r1 0/8, r2 passed. | trials.tsv; DS r1 transcript |
| process-compose-s2 | b6 | solved both (DS 15) | 3 traps in two folders; one host-check middleware covers all. Injected `legacy.go` opened at 0.2. | DS r1 transcript |
| claw-orchestrator-s2 | b5 | solved both (DS 10) | 3 of 5 traps in one function of `embedded-server.ts`. Both injected traps are lines 146-155 of that function. | manifest traps |
| n8n-node-sqlite3-s2 | b5 | solved both (DS 10) | Tiny repo; all 6 traps are variants of one path option in one node package. The candidate came from an already-solved stacked task. | manifest; pool_sources.tsv |
| praisonai-s2 | b6 | solved both (DS r2, MiMo r3) | 5 missing-auth routes, same token idiom, found at 0.1-0.3. DS r1 missed 2 routes, MiMo missed more in r1-r2. A near-breaker lost to run-to-run variance. | fails per run (tools/fails.py) |
| piscina-s2 | b6 | solved both (DS 12) | 6 of 7 traps in `src/index.ts`. One "own properties only" rule fixes every options object. The instruction says the rules "apply to every options object". | manifest; instruction |
| middleware-s2 | b5 | solved both (DS 13) | 8 OAuth provider files with copied identical state-check code: "more routes of one concept", which the brief says never to add. DS edited all 8 within 0.1 min of each other. | manifest T1/T5; DS r1 transcript |
| hurl-s2 | b6 | solved (DS 9; MiMo r1 also 1.0 in ledger) | All 5 traps in `client.rs`/`options.rs`. DS changed 2 files. | manifest; final-code |
| mcp-context-forge-s2 | b5 | DS solved r1; MiMo 2 fails then pass | 3 traps in 2 files. MiMo failed through functional breakage and API cuts, not by missing sites. | fails per run |
| pi-s2 | b5 | DS 2 fails then pass; MiMo pass | Near-breaker. DS missed the extension loader's second discovery path in 2 of 3 runs. All files opened by 0.3. | fails per run |
| infracost-s2 | b5 | DS 2 fails then pass; MiMo 1 fail | Near-breaker. Registry token/host check was the last site, edited at 22 min. | fails per run; DS r3 transcript |
| kuma-s2 | b5 | **breaker** (delivered) | Held on one real route: `tools/xds-client` dials with `InsecureSkipVerify` and an upstream comment says this is "acceptable as this is only to be used in testing". DS saw it in its first grep at 0.0 and decided "test client. Leave." in every run. MiMo also left the `apply` URL fetch. A scope judgement, not a search problem. | DS r1 transcript (grep "xds-client"); verifier results |
| medplum-s2 | b6 | **breaker** (kept) | Held on a shape. The instruction gives two rules: redirect URIs must match exactly; allowed destinations may extend at a path-segment boundary. Every run (7) applied the segment rule to redirect URIs too, failing the same 4 tests. All trap files opened by 0.4. | instruction; fails per run |
| stk-liferay-portal-ghsa3qq5 | b1 | **breaker** | Held on distance. Two of three traps are other real advisories in other modules. DS never opened `PortletContainerUtil`; both models fixed `PortalImpl` only. 3/7 in all 6 runs. | open_all.tsv; fails per run |
| stk-commonmark-ghsajjv6 | b1 | **breaker** | Held on distance. 3 of 4 traps are in the Attributes extension, which neither model opened in r1. 2/8 in all 7 runs. | open_all.tsv; fails per run |
| nono-s2 | b3 | **breaker** | Held on one route: pack defaults used in a dry run. All trap files opened by 0.2. 16/17 in every run. | fails per run |
| browsershot-s3 | b3 | **breaker** | Held on a second-order shape: local file references inside a supplied HTML document (absolute and traversal). Models guarded URLs and paths only. 9/11 in all 6 runs. | fails per run |
| spark-s3 | b3 | solved both (DS 8) | 7 XSS traps, all in `historypage.js`. One escaping pass covers them. | manifest |
| tilt-s2 | b3 | solved both (DS 46, after regrade) | 8 traps, all in `internal/hud/server` plus a CLI helper. One origin/token check covers them. | manifest; regrade dirs |

Counts from the sample:
- 16 of 16 solved tasks: every real trap file was opened in DeepSeek's first run, 14 of 16 within 3 minutes.
  The misses are reference-fix or helper files, not trap sites. First edit came at 1.8-6.6 minutes.
- 12 of 16 solved tasks: the traps are copies of one idiom, or sit in one file or one package, so one change
  covers them (phpsysinfo, wakaru, ts-stack, hydro, process-compose, claw, n8n, piscina, middleware, hurl,
  spark, tilt).
- 4 of 16 solved tasks were near-breakers that one model failed 2 of 3 times (praisonai, pi, infracost,
  mcp-context-forge). At those rates, 3/3 is a coin flip, so the batch yields carry real noise.
- 4 sibling breakers (kuma, medplum, nono, browsershot): all trap files opened early. They held on judgement:
  2 shapes, 1 route left on purpose, 1 route the solver did not connect.
- 2 stacked breakers (liferay, commonmark): they held because the other advisories' code was never opened.

Across all batches (DeepSeek r1, `open_all.tsv`; trap files by name, so this is approximate):

| | Tasks | All trap files opened within 3 min | Some trap file never opened |
|---|---|---|---|
| Sibling, DS solved | 204 | 160 (78%) | 20 |
| Sibling, DS failed 3/3 | 44 | 30 (68%) | 7 |
| Stacked, DS solved | 44 | 32 (73%) | 9 |
| Stacked, DS failed 3/3 | 39 | 16 (41%) | 15 |

Sibling fails mostly happen with every site already found. Stacked fails are often sites never found.

## 3. b5-b6 against the b1/b3 contrast

- **Advisory and repo:** b5-b6 candidates come from the sibling pool. By router design (`pipelines/router/README.md`),
  that pool holds repos the stacking selector did not take (step 2) plus repos whose stacked task was already
  solved (step 3, merged into the general pool on 10-27). So it is the remainder after the best-first stacking
  pass. 8 of 110 b5-b6 tasks came from solved stacked tasks; 1 of those 8 is a DS fail (`djust-s2`), about the
  same rate as the others.
- **Trap design:** same brief Design section for b3 and b5-b6 (diffed `tilt-s2` against `kuma-s2`). Builders
  call their main lever "how-type" in `notes.md` (middleware, piscina, hurl), but the solvers fix those levers
  within minutes. The brief has no check that a lever is really how-type.
- **Instruction:** about the same in b3 and b5-b6: median 388 words in b3 against 405 and 395, with sweep phrases
  ("however it is reached", "every part…") in 43% against 37% and 47%. Across all sibling tasks, instructions with
  a sweep phrase have half the DS fail rate (12/106 = 11% against 33/145 = 23%). Sibling instructions under 300
  words failed DS 10/24 (42%). Stacked instructions are short (median about 250 words) and almost never have a
  sweep phrase (5%). This is a correlation and may be partly the recipe. I count it as suspected.
- **Tests:** same structure and wrong-fix catalogue in all sibling batches (60/60, 69/69, 59/59, 58/58 manifests).
  The newer test-quality rules lower false breakers, see Caveat B.

## 4. Selection side

- **Later batches do come from lower scores.** Median combined score: b2 8.6, b3 8.3, b4 8.0, b5 7.67, b6 5.0.
- **But the score does not predict outcome inside a pass.** In the 10-27 combined pass (b5-b6), DS-fail tasks
  had median score 5.17 against 5.33 for solved tasks. Top half by score: 8 of 70 DS-fail. Bottom half: 8 of 40.
  The pre-b5 pass (b2-b3): top half 6/26, bottom half 6/21. b6, the lowest ranks, has more DS fails than b5.
- **Screener features do not predict either:** entry points, distance, uncovered routes, injection room and fix
  minutes have nearly equal medians for DS-fail and DS-solved tasks. DS-fail tasks have slightly *fewer* entry
  points (2.5 against 3.0).
- **The selector's reasons are one template:** "second impl + N uncovered routes; coupled X". They reward the
  count of sites and routes. Those are exactly the where-type levers the solvers clear in minutes.
- **The stacking score does predict.** Top half of stacked tasks: 18/46 both-fail (39%). Bottom half: 11/46
  (24%). The bottom stacking quartile (score 0.05-0.22) still made 6/23 both-fail and 3 delivered. That beats
  the sibling recipe.
- **Stacking supply:** 771 repos were screened for stacking. 111 usable stacked designs came out, and about 95
  were built in b1-b2. So the screened stacking pool is nearly used up. The index has many more multi-advisory
  packages: `h12_summary.md` lists 916 mid-size groups (3-8 co-present advisories), most not screened.

## 5. Ranked causes

Shares are rough and refer to the drop from 37% (b1 as given) to 2% (b5-b6 as given).

| Rank | Cause | Status | How much it explains |
|---|---|---|---|
| 1 | Recipe mix: stacking (about 31% both-fail, b1-b2) replaced by siblings (about 15%, b2-b4) after the stacking pool ran out | Measured | About half. Siblings never yielded more than 20% in any batch. |
| 2 | Censoring of b5-b6: failing tasks still in trials or audit when measured | Measured | Most of the gap from ~10% to 2%: 3 awaiting audit in b5, 1 in b6, 7-8 DS-failed tasks pending. |
| 3 | Sibling trap design: siblings share the reported idiom and are found by the first grep; one helper fixes all | Measured (mechanism); sets the sibling ceiling, not a b3→b5 change | Explains why siblings sit at ~10-15%, not why they fell. |
| 4 | Inflated early figures: dropped/withdrawn breakers counted (b1 5, b3 3) | Measured | b1 37%→28%, b3 17%→11%. |
| 5 | Within-sibling decline b3 (26% DS fail) to b5 (11%) | Measured, weak (p≈0.04 for b3 against b5; b6 is back at 19%) | Small; mostly noise from near-breakers. |
| 6 | Test repairs and regrades turning fails into passes | Measured, all batches | 1-6 tasks per batch; not batch-specific. |
| 7 | Weaker candidates in later ranks | Not supported | Score does not predict; b6 (lowest ranks) beats b5. |
| 8 | Lint step (b5+) telling builders to name the layer in the instruction for direct-drive tests | Suspected, unmeasured | Possibly a few pointer sentences. |
| 9 | Claude Code 2.1.310 → 2.1.312 | Suspected, no evidence | Sibling DS rates were flat across the change. |

## 6. Recommendations

1. **Put stacking back as the main recipe, and refill its pool.** (Cause 1.) Screen more multi-advisory repos
   from the H1/H2 groups (916 mid-size groups, most not screened) and run the stacking reader on them. Even the
   bottom stacking quartile beat the sibling recipe. Report yield per recipe, never mixed.
2. **Measure yield on complete cohorts only.** (Causes 2 and 4.) Report a batch only when every task has a final
   verdict. Until then show "confirmed / pending audit / DS-failed with MiMo pending". Report kept/delivered
   breakers separately from raw both-fail. Count rate-limit-cut runs as no-run, not as fail.
3. **Change the sibling brief so traps cannot be found by the reported idiom.** (Cause 3.)
   - Drop or cap where-type siblings that copy the reported idiom (middleware's 8 identical providers, phpsysinfo's
     header-reading copies). Treat them as zero difficulty.
   - Require at least one lever of the kinds that held: a shape the plausible fix gets wrong (medplum, browsershot),
     a wrong object or missing authority (mollieplugin, core, migration-planner), ordering (wasmtime), or a route
     whose own code argues it is out of scope (kuma, nono). Keep it fair: the general property must cover it.
   - Check that Contracts do not hand over the design of the how-type lever. In phpsysinfo the Contracts give the
     trusted-proxy key, format and meaning, so that lever was free.
4. **Add a cheap gate check for discoverability.** (Cause 3.) Grep the pinned tree for the identifiers on the
   report's path (the sink, the header, the config key). If every trap file appears in those results, flag the
   task as "found by one grep". In this audit, such tasks were solved almost every time.
5. **Stop spending selection effort on the sibling score as it is.** (Cause 7.) It does not predict. Either
   recalibrate it on the 230 finished sibling tasks (DS fail as the label), or rank by features that relate to
   holds: an advisory with a shape-type fix, a wrong-object check, or a real route with an in-code reason to
   dismiss. Do not rank by route counts.
6. **Run a fourth DeepSeek attempt only for near-breakers if the owner wants less noise.** (Cause 5.) Four of
   16 solved sample tasks were 2/3 fails. This does not raise yield. It only makes the per-batch figures
   steadier. It is optional.

Top 3: recommendations 1, 2 and 3.

## 7. Limits

- "Opened" uses file basenames from the manifest, so common names (`index.ts`, `client.go`, `main.rs`)
  overstate discovery a little.
- b6 is still moving: the both-fail count went from 7 to 8 in the ledger while I was working.
- I did not judge fairness of any breaker. kuma's hold (a test tool the upstream comment marks as test-only) is
  the kind of hold a fairness reviewer may question.
- The p-value for b3 against b5 is a rough Fisher estimate on DS-fail counts (14/54 against 6/57).
