# MITRE CWE and CWE Top 25: research findings for the screener

_Research item 2 of [../taxonomy_research.md](../taxonomy_research.md). Compiled 2026-10-16._

## Summary

1. **Public per-CWE LLM repair data exists.** It was gathered under item 1: CWE-bench per-CWE
   results for 73 CWEs (DeepSeek V4.1 Flash included), plus about 15 repair studies. See
   [owasp_top10_findings.md](owasp_top10_findings.md). It is already in the screener as the
   per-CWE adjustments in `sourcer/weights.json`.
2. **Abstraction level is a real signal, but MITRE's "Class" label is too coarse to score.**
   - On CWE-bench, DeepSeek passes 47% of tasks at the Class level vs 59% at Base and 64% at
     Variant, which agrees with CWEFT. Across all 11 models the gap is small (56 vs 59).
   - Scoring every Class-level CWE fired on 31% of candidates, mostly 862, 863 and 287. These
     are everyday labels, not vague ones.
   - The screener therefore scores only genuinely broad CWEs (20, 264, 269, 284, 693, 707),
     Pillars, and non-weakness category numbers: 57 candidates.
3. **Top 25 CWEs are *easier* for models, not harder.** On CWE-bench, DeepSeek passes 67% of
   tasks on the 14 Top 25 CWEs vs 52% on the other 59 (all models: 62% vs 57%). The most common
   weaknesses are the best known. This puts realism (good for the client) against difficulty
   (our goal). **Decided 2026-10-16: option (c), label only (0 points).** 921 of 1,462 candidates carry it.
4. **The hierarchy fills category gaps.** A CWE missing from OWASP's lists now takes the
   category of its nearest mapped ancestor in MITRE's Research view (CWE-1000). Unmapped
   candidates fell from 173 to 71.

## Data (in this folder)

| File | What |
|---|---|
| `sources/mitre/cwec_v4.20.xml` | MITRE CWE catalogue 4.20 (2026-04-30), verbatim |
| `sources/mitre/top25_2025.html` | the 2025 CWE Top 25 page, verbatim |
| `cwe_hierarchy.tsv` | 969 weaknesses with abstraction, Research-view parent, pillar, depth and path (10 Pillar, 114 Class, 539 Base, 299 Variant, 7 Compound) |
| `cwe_top25_2025.tsv` | rank, CWE, score, CVEs in KEV, rank change vs 2024 |
| `extract_cwe_hierarchy.py` | regenerates both tables from the sources |

## 1. Abstraction level vs repair success (CWE-bench v1, task-weighted pass@1)

| Abstraction | CWEs | Tasks | DeepSeek V4.1 Flash | 11-model mean |
|---|---|---|---|---|
| Pillar | 2 | 4 | 31.5 | 50.6 |
| Class | 19 | 29 | **46.6** | 55.5 |
| Base | 45 | 76 | 58.9 | 59.2 |
| Variant | 5 | 9 | 63.9 | 64.0 |
| not a weakness entry (16, 310) | 2 | 2 | 25.0 | 37.5 |

**Corroboration:** CWEFT (ESEM 2026, Java) found "repair rate tracks how concrete the
vulnerability class is". CWE-20 was repaired 3.1% of the time and 284/264/269 0%.

**Why not score every Class:** MITRE's Class level includes 287, 863 and 862. These are
standard, specific-in-practice labels; CWE-bench has 287 at 100%. Scoring all Classes fired on
31% of the pool and would have rewarded A01 again. The curated broad list fires on 4%.

## 2. CWE Top 25 (2025) vs repair success

| Group | CWEs | Tasks | DeepSeek | 11-model mean |
|---|---|---|---|---|
| in the 2025 Top 25 | 14 | 24 | **66.8** | 61.8 |
| not in the Top 25 | 59 | 96 | 51.8 | 57.1 |

**Notes:**
- **Why easier:** Top 25 CWEs are the most frequent in CVEs, so they are the most represented
  in training data and fix examples.
- **Agreeing sources:** generation and repair sources show the same pattern for the textbook
  ones. SQLi (89) and OS command injection (78) are easy everywhere. XSS (79) and path
  traversal (22) are disputed (item 1).
- **The Top 25 also carries KEV counts** (CVEs known to be exploited). That feeds research
  item 4c.

**Options for the screener. Decided: (c), label only.** Revisit once our own trials give per-model evidence.

| Option | Points for a Top 25 CWE | Effect |
|---|---|---|
| (a) difficulty | −1 | follows the evidence: Top 25 CWEs are easier |
| (b) realism | +1 | rewards weaknesses the client will recognise |
| (c) label only | 0 | records Top 25 membership for analysis; changes nothing |

## 3. Category gaps filled through the hierarchy

- **Before:** 173 candidates had no OWASP category.
- **Rule:** a CWE not in any OWASP list takes the category of its nearest ancestor that is
  listed, in the Research view.
- **Examples:** CWE-346 and 348 → 345 (A08); 367 → 362 (A06); 1289 → 20 (A05); 1385 → 346
  (A07); 754 → 703 (A10).
- **After:** 71 candidates stay unmapped. Those CWEs have no mapped ancestor, mostly resource
  exhaustion (400), algorithmic complexity (407, 1333) and memory allocation (789).
- **Adjustments are not inherited.** The per-CWE ±points apply only to the exact CWE, because
  siblings vary too much in CWE-bench.

**Also fixed:** in the first version of weights v2, the screener took the best CWE's total, and
"unmapped" (+1) outscored A01 (0). A candidate with CWE-863 plus an unmapped CWE-400 was
labelled "unmapped". Now:
- the category comes from the best CWE that maps;
- the adjustment is the highest over all the candidate's CWEs.

## 4. Effect on the ranking (vs the original v1 ranking, 1,462 candidates)

| Measure | Value |
|---|---|
| top-20 / top-50 / top-100 overlap with v1 | 6 / 24 / 64 |
| favoured candidates | 857 (v1) → 448 |
| top-50 by category | A06 17, A01 11, A05 10, A08 9, A07 3 (v1: A01 21) |

## 5. For experiment planning: siblings through the hierarchy (not scored)

- **Rule:** siblings for injection are different Base or Variant CWEs under the same parent
  Class, read from `cwe_hierarchy.tsv` (`parent` column).
- **Example:** 862 Missing Authorization and 863 Incorrect Authorization both sit under 285
  Improper Authorization.
- **Status:** this gives a precise "same class, different variant" for building sibling tasks.
  It is not wired into the screener, because it describes task construction, not candidate
  difficulty.
