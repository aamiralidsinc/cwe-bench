# Item 4: CVSS, EPSS and CISA KEV vs LLM repair success

Research date 2026-10-15/16. Tracker: [../taxonomy_research.md](../taxonomy_research.md) items 4a–4c.
Raw material: [raw/item4-severity/](raw/item4-severity/) (scripts, tables, outputs, agent reports);
bulk downloads in `~/.tb-graders/cwe/research-raw/item4-severity/` (see its `INDEX.md`).

## Bottom line

- **Nobody has published this relation.** No repair paper reports success by CVSS, EPSS or KEV.
  LiL (arXiv 2605.28893) uses CVSS only as a control variable and gives no coefficient for it.
  So we computed it ourselves from public per-task, per-model results.
- **CVSS: high/critical CVEs are fixed slightly *more* often, not less.** The difference is +4.7
  points within each benchmark (p = 0.026), and 11 of 13 benchmarks point that way. The effect is
  small and fragile: without PatchEval p = 0.12, and after correcting for three tests p ≈ 0.08.
  DeepSeek runs alone: +5.0 points, p = 0.15.
- **EPSS: no relation** (+0.9 points, p = 0.65; DeepSeek +4.3, p = 0.21). The direction flips
  from benchmark to benchmark.
- **KEV: cannot be tested.** Only 5 of the 922 CVEs are in CISA KEV.
- **Screener change: none.** No signal is strong enough to score. If anything, a high CVSS makes
  a candidate marginally *less* likely to break models, the opposite of what one might hope.
  Severity stays a descriptive field to record per task, not a score.

## What we measured

**Data.** 13 sources publish which model fixed which CVE. Each source uses its own success rule.

| Source | Language | CVEs | Runs used | DeepSeek runs | Success rule |
|---|---|---|---|---|---|
| LiveCVEBench | 14 langs | 190 | 29 | V3.1-Terminus, V3.2 (5) | leaderboard `success` |
| PatchEval (direct LLM) | Go/JS/Py | 230 | 9 | V3, R1-0528 | any epoch `success` |
| SEC-bench | C/C++ | 200 | 7 | – | report `success` |
| BountyBench | Py/JS | 40 | 10 | R1 (C-Agent) | patch within 3 attempts |
| Gatti CVE-Bench | Python | 19 | 18 | – | author's rule |
| VulnRepairEval | Python | 23 | 6 | V3, R1 | PoC no longer works |
| APPATCH | C (kernel) | 97 | 7 | Coder-V2 | patch labelled correct or plausible |
| CWEFT | Java | 42 | 12 | – | L3 (compiles, PoV fails, no regressions) |
| SAN2PATCH | C | 33 | 6 | – | paper Table 3 |
| Pearce 2023 | C | 11 | 6 | – | functional + security tests pass |
| Wu ISSTA 2023 | Java | 48 | 6 | – | manually judged correct |
| Garg 2025 (real only) | Java | 13 | 14 | R1-Distill-32B | paper Table 2 |
| "Why LLMs Fail" | Java | 61 | 1 (Gemini 3 Flash) | – | any of 5 samples correct |

12,543 results on 907 CVEs. 17 runs that solve under 5% of their CVEs are dropped because they
carry no signal. Most are pre-LLM repair tools; the others are two broken-looking LiveCVEBench
OpenHands runs and six weak models in VulnRepairEval.

No source tests Xiaomi MiMo. Full per-task transcripts exist only for SEC-bench (GPT-5.x runs),
Gatti and APPATCH. The full inventory, including dead ends, is in
[raw/item4-severity/02-inventory-benchmark-suites.md](raw/item4-severity/02-inventory-benchmark-suites.md)
and [03-inventory-academic-studies.md](raw/item4-severity/03-inventory-academic-studies.md).

**Severity.**
- **CVSS:** NVD primary base score, preferring v4.0, then 3.1, 3.0, 2.0. Taken from NVD's bulk
  yearly feeds (downloaded 2026-10-15) plus earlier API records.
- **EPSS:** current FIRST scores.
- **KEV:** current CISA catalogue.
- **Coverage:** 917 of 922 CVEs have CVSS and EPSS.

**Method.**
- **Unit:** one CVE within one benchmark, scored by the share of that benchmark's runs that fixed it.
- **Comparison:** made inside each benchmark, because benchmarks differ hugely in difficulty, then
  averaged with weights by number of CVEs.
- **p-values:** severity labels are shuffled among CVEs inside each benchmark (stratified
  permutation, 4,000 shuffles), so a benchmark's difficulty cannot fake an effect.
- **Splits:** CVSS ≥ 7.0 vs below; EPSS above vs below each benchmark's own median (benchmark CVEs
  skew to high EPSS, so a fixed cut gives lopsided groups).

## Results

### CVSS ≥ 7.0 vs < 7.0 (all runs)

| Benchmark | High/critical: n, fixed | Below 7: n, fixed | Difference |
|---|---|---|---|
| APPATCH | 42, 42.3% | 51, 31.3% | +11.0 |
| BountyBench | 31, 62.3% | 9, 41.1% | +21.1 |
| CWEFT | 23, 18.8% | 19, 13.6% | +5.2 |
| Garg 2025 | 9, 41.3% | 4, 26.8% | +14.5 |
| Gatti | 14, 37.7% | 5, 62.4% | −24.7 |
| LiveCVEBench | 97, 22.5% | 93, 28.7% | −6.2 |
| PatchEval | 146, 44.0% | 84, 35.4% | +8.5 |
| Pearce 2023 | 4, 58.3% | 7, 57.1% | +1.2 |
| SAN2PATCH | 10, 55.0% | 23, 41.3% | +13.7 |
| SEC-bench | 113, 44.1% | 87, 39.1% | +5.0 |
| VulnRepairEval | 17, 15.7% | 6, 5.6% | +10.1 |
| "Why LLMs Fail" | 35, 31.4% | 25, 28.0% | +3.4 |
| Wu ISSTA 2023 | 22, 16.7% | 26, 12.8% | +3.8 |
| **Combined** | | | **+4.7, p = 0.026** |

**Robustness** ([cvss_leave_one_out.txt](raw/item4-severity/cvss_leave_one_out.txt)):
- **Leave one out:** dropping any single benchmark keeps the sign (+3.5 to +7.2). p stays below
  0.07 except without PatchEval (0.12).
- **Shared CVEs:** dropping the Java studies that reuse Vul4J CVEs (CWEFT, "Why LLMs Fail", Garg)
  changes nothing (+4.6, p = 0.031).
- **Not checked:** whether the effect comes from the weakness type rather than severity itself.
  For example, high-CVSS injection bugs may simply be easy to fix (see item 1).

### EPSS above vs below median (all runs)

Combined +0.9 points, p = 0.65. Seven benchmarks are positive and six negative. PatchEval (+12.4)
and VulnRepairEval (+16.3) say "more exploitable = easier"; Garg (−40), Pearce (−29), Gatti (−27)
and "Why LLMs Fail" (−13) say the opposite. There is no consistent relation.

### KEV

5 CVEs are in KEV:
- CVE-2016-3081 (CWEFT, "Why LLMs Fail")
- CVE-2021-43798 (PatchEval)
- CVE-2025-23209, CVE-2025-32433, CVE-2025-3248 (LiveCVEBench)

Too few to test (p = 0.64). Repair benchmarks pick CVEs with a clean fix commit and a
reproducible build, which rarely overlaps with what attackers exploit in the wild.

### DeepSeek runs only

| Signal | Combined difference | p | Benchmarks |
|---|---|---|---|
| CVSS ≥ 7.0 | +5.0 | 0.15 | 6 |
| EPSS above median | +4.3 | 0.21 | 6 |
| KEV | +4.6 | 0.84 | 2 (4 KEV CVEs) |

Same direction as all runs, weaker evidence (555 units vs 1,007).

## What this means for us

1. **Do not use severity to find breakers.** It does not predict failure. If CVSS predicts
   anything, it is a slightly *higher* fix rate.
2. **Record severity, don't score it.** CVSS, EPSS and KEV stay descriptive fields on each
   candidate (taxonomy item 3, enrichment) so they can be reported per task. `weights.json` is
   unchanged.
3. **Revisit with our own trials.** Once we have 50+ (task, model) verdicts, rerun the same split
   on our own data. Our 16 trialled task CVEs are listed in
   [raw/item4-severity/our_task_cves.txt](raw/item4-severity/our_task_cves.txt); 16 is too few now.
4. **KEV is a selling point, not a difficulty lever.** A KEV-listed task could be attractive for
   realism, but candidates will rarely have it.

## Limits

- Success rules differ by source (PoC-only, PoC + tests, manual judgement). Comparing inside each
  benchmark handles the level but not the meaning.
- EPSS and KEV are today's values, not the values at the time the benchmarks were built.
- The CVSS source is mostly NVD; 13 CVEs have only CVSS v2.
- APPATCH has three model columns whose totals differ from the paper (GPT-4, Claude, Llama).
  PatchEval's "any epoch" rule reproduces DeepSeek V3's leaderboard score but not R1's.
- No source covers MiMo, and DeepSeek coverage is older models (V3, R1, V3.1/V3.2), not V4.1 Flash.
