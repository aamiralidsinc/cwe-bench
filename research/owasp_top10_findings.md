# OWASP Top 10:2025: research findings for the screener

_Research item 1 of [../taxonomy_research.md](../taxonomy_research.md). Compiled 2026-10-16.
Data files in this folder are generated from verbatim source copies (see "Sources")._

## Summary

1. **Localisation is the most consistent predictor in every source, more than CWE, category or
   fix size.** It means the fix belongs away from where the bug shows (wrong layer, off the
   crash stack):
   - PatchBench: agents "guard the symptom with incomplete local checks", the most common
     failure;
   - SWE-bench's never-solved tasks: wrong architectural layer in 10 of 12;
   - VulnRepairEval: 60–78% of failures.

   **Fix shape matters, but its effect varies by source.** It is strong in PatchEval (20% at
   1 file vs 0% at 3+; 25% at 1 hunk vs ≈0% at 3+), modest in SEC-bench (75% vs 63% for
   multi-file), and not significant among SWE-bench's never-solved tasks.

   So symptom–fix disparity (S2) deserves the most weight but is measured only weakly today
   (section 7). Fix shape (S6) is a solid secondary signal.
2. **Among categories, only the extremes are reliable.**
   - **Hardest in two CWE-bench versions:** A08 Integrity (DeepSeek 39%) and A06 Insecure
     Design (42%).
   - **Easiest:** A01 Access Control and A04 Crypto (65%).
   - **The middle categories reshuffled between versions:** "the verifiers moved more than
     the models".
3. **The current screener rewards the wrong things.** Its yes/no S5 bonus favours
   access-control and basic-auth CWEs, among the *easiest*: CWE-285 at 100%, 287 at 100%,
   918 at 96%. It penalises some of the hardest for DeepSeek: open redirect 601 and template
   injection 1336, both 0%.
4. **Abstract weakness classes are the hardest to repair.** CWE-20 is repaired 0–3% in two
   Java studies, and 284/264/269 0%. The sourcer currently just skips these labels when naming
   a weakness.
5. **Hard across several sources:** integrity/authenticity, deserialisation, session and
   rate-limit logic, races, request smuggling, log leaks, use-after-free and uninitialised
   memory.
6. **Easy across several sources:** OS command injection, SQLi, weak crypto parameters and
   bounds checks.
7. **Sources disagree on** path traversal, XSS, code injection and SSRF.
8. **Two directions are backed by outside evidence:**
   - **Injected variants:** they drop every model to 0–20% (Garg et al.), which supports our
     sibling injection.
   - **LLM-in-the-loop bugs:** a source class we don't screen for yet. DeepSeek-V4-Pro scored
     0/4 on output rendering.
9. **No MiMo data is published anywhere.** MiMo's weights can only come from our own runs.

## Sources

| Key | What | Where in repo |
|---|---|---|
| CWE-bench v1 | per OWASP category × model and per CWE × model pass@1, 120 tasks, 73 CWEs, 11 models incl. DeepSeek V4.1 Flash (snapshot 2026-09-26) | `sources/cwe-bench-site/` (verbatim) → `cwe_bench_v1_category.tsv`, `cwe_bench_v1_cwe.tsv` via `extract_cwe_bench.py` |
| OWASP Top 10:2025 | official category → CWE mapping (final edition), 249 CWEs | `owasp2025_cwe_map.json` |
| BaxBench (ICML 2025) | secure code *generation*, per-CWE insecure rates for DeepSeek-R1/V3 and others | quoted below (generation, not repair) |

**How the CWE-bench numbers were obtained:**
- **Category numbers:** read from the paper's Figure 5, a vector PDF in the arXiv source with
  the values embedded as text.
- **Per-CWE numbers:** from the site's data file.
- **Cross-check:** the two sources agree, and the per-CWE values task-weight back to every
  category cell within 1 point.
- **Spot-check:** we checked several cells against the raw files ourselves.

## 1. Category ranking (CWE-bench v1, pass@1, %)

| Rank (hardest first) | Category | Tasks | DeepSeek V4.1 Flash | 11-model mean | Best model |
|---|---|---|---|---|---|
| 1 | A08 Software or Data Integrity Failures | 11 | **39** | 36.4 | 57 |
| 2 | A06 Insecure Design | 12 | **42** | 47.7 | 67 |
| 3 | A10 Mishandling of Exceptional Conditions | 13 | 52 | 57.4 | 77 |
| 4 | A05 Injection | 14 | 54 | 57.3 | 89 |
| 5 | A09 Security Logging and Alerting Failures | 10 | 55 | 58.2 | 75 |
| 6 | A02 Security Misconfiguration | 11 | 57 | 62.1 | 75 |
| 7 | A07 Authentication Failures | 13 | 58 | 51.8 | 63 |
| 8 | A03 Software Supply Chain Failures | 10 | 60 | 59.5 | 75 |
| 9 | A01 Broken Access Control | 13 | 65 | 71.9 | 92 |
| 10 | A04 Cryptographic Failures | 13 | 65 | 74.8 | 90 |

The site's own summary agrees: "models share weaknesses in data integrity (A08), insecure
design (A06), and authentication (A07)".

**Context for DeepSeek:**
- Across 4 attempts, it solves all 4 on 43 tasks, 1–3 on 46, and none on 31.
- So about a quarter of CWE-bench-level tasks are pass@4 = 0 for DeepSeek.
- By language, DeepSeek is weakest on Java (46), Python (46) and Rust (42, but only 3 tasks).

## 2. Inside each category: what DeepSeek fails, what is saturated

CWE-bench per-CWE pass@1. Most CWEs have **1–2 tasks**, so a value mainly describes that
one task's design, including its injected variants, not the CWE in general. Treat it as a
signal, not a law. Full table: `cwe_bench_v1_cwe.tsv`.

### Hard for DeepSeek (≤ 25%)

| Cat | CWE | Tasks | DeepSeek | 11-model mean | Models at 0 |
|---|---|---|---|---|---|
| A06 | 444 HTTP request smuggling | 1 | 0 | 0.0 | 11/11 |
| A07 | 307 Excessive auth attempts | 1 | 0 | 0.0 | 11/11 |
| A08 | 345 Data authenticity verification | 1 | 0 | 0.0 | 11/11 |
| A03 | 1357 Insufficiently trustworthy component | 2 | 0 | 2.3 | 10/11 |
| A06 | 362 Race condition | 1 | 0 | 2.3 | 10/11 |
| A06 | 913 Dynamically-managed code resources | 1 | 0 | 9.1 | 9/11 |
| A10 | 252 Unchecked return value | 1 | 0 | 9.1 | 10/11 |
| A08 | 502 Deserialization | 2 | 0 | 9.2 | 7/11 |
| A01 | 601 Open redirect | 1 | 0 | 13.6 | 8/11 |
| A02 | 310 Cryptographic issues | 1 | 0 | 22.7 | 8/11 |
| A05 | 1336 Server-side template injection | 2 | 0 | 24.1 | 3/11 |
| A10 | 674 Uncontrolled recursion | 1 | 0 | 50.0 | 2/11 |
| A06 | 693 Protection mechanism failure | 2 | 13 | 53.5 | 0/11 |
| A07 | 613 Insufficient session expiration | 2 | 25 | 20.5 | 5/11 |
| A08 | 494 Download without integrity check | 1 | 25 | 22.7 | 5/11 |
| A05 | 79 XSS | 2 | 25 | 29.7 | 3/11 |
| A02 | 942 Permissive CORS policy | 2 | 25 | 44.5 | 0/11 |
| A05 | 93 CRLF injection | 3 | 25 | 47.7 | 0/11 |
| A04 | 347 Signature verification | 2 | 25 | 54.6 | 0/11 |
| A01 | 497 Sensitive system info exposure | 1 | 25 | 61.4 | 0/11 |
| A01 | 441 Unintended proxy | 1 | 25 | 63.6 | 3/11 |

**Hard for DeepSeek but not for other models:** 674 (field 50%), 693 (54%), 347 (55%),
497 (61%), 441 (64%). These are the most model-specific weak spots, and the best evidence
for a DeepSeek-targeted weight.

### Saturated (11-model mean ≥ 90%, DeepSeek 100%): drop or penalise

| Cat | CWE | Tasks | DeepSeek | Mean |
|---|---|---|---|---|
| A01 | 22 Path traversal | 1 | 100 | 97.7 |
| A01 | 285 Improper authorization | 1 | 100 | 100.0 |
| A01 | 918 SSRF | 2 | 100 | 95.6 |
| A03 | 1104 Unmaintained component | 3 | 100 | 96.2 |
| A04 | 319 Cleartext transmission | 1 | 100 | 90.9 |
| A04 | 330 Insufficient randomness | 2 | 100 | 93.3 |
| A04 | 916 Weak password hash | 2 | 100 | 97.8 |
| A05 | 470 Unsafe reflection | 1 | 100 | 95.5 |
| A06 | 434 Unrestricted upload | 1 | 100 | 97.7 |
| A07 | 287 Improper authentication | 1 | 100 | 100.0 |

These match our own experience: py-shiny (CWE-22), async-http-client and rclone (CWE-287) were
solved easily by both models.

### Per category, in words

- **A08 (hardest):** deserialization (502), data authenticity (345) and integrity of downloads
  (494) are near 0 everywhere. Only cookie validation (565) and prototype pollution (1321)
  are moderate.
- **A06:** request smuggling (444) and race conditions (362) are unsolved by nearly everyone.
  Upload validation (434) is saturated, so A06 is not uniformly hard.
- **A07:** the category average hides a split. Basic authentication (287) is 100%, but
  rate-limiting (307), session expiry (613), missing-auth (306) and alternate-path bypass
  (288) are all hard.
- **A01:** mostly easy: 22, 285 and 918 are saturated, and 862/863 are 63–75% for DeepSeek.
  The exceptions are open redirect (601, 0%), unintended proxy (441) and info exposure (497).
- **A04:** easy overall, except signature verification (347, DeepSeek 25%) and broken crypto
  algorithms (327, 33%).
- **A05:** the textbook sinks are easy (SQLi 89 at 100%, reflection 470). XSS (79), CRLF (93)
  and SSTI (1336) are hard for DeepSeek.

## 3. CWE-bench vs the official OWASP mapping

64 of CWE-bench's 73 CWEs are in the official 2025 lists, all in the same category. The other
9 are **not mapped by OWASP at all**, so CWE-bench assigned them itself:

| CWE | CWE-bench's category |
|---|---|
| 310 | A02 |
| 208 | A04 |
| 1336 | A05 |
| 770, 913, 1284 | A06 |
| 354, 1321 | A08 |
| 674 | A10 |

**For the screener:** map a CWE with the official 249, then CWE-bench's 9 extensions. Mark
anything else **unmapped**; walking up the CWE hierarchy can come later.

**Mapping errata to handle:**
- OWASP's A03 lists CWE-447, a known typo for **477**.
- CWE-16 and 320 are obsolete categories, not weaknesses.
- Common CWEs such as memory safety, 400 and 1333 are in no category.

## 4. Secure-code generation evidence (BaxBench, secondary)

BaxBench measures **generation**, not repair: how often generated backends are exploitable,
per CWE, no security prompt (Appendix D.2, Table 12). The rate is the share of
functionally-passing backends that are exploitable, so **higher is worse**.

| CWE | DeepSeek-R1 | DeepSeek-V3 | Best model in paper |
|---|---|---|---|
| 79 XSS | 0.83 | 0.84 | 0.70 |
| 117 log neutralisation (1 scenario) | 0.91 | 1.00 | 1.00 |
| 522 credential protection | 0.37 | 0.30 | 0.23 |
| 400 resource consumption | 0.35 | 0.47 | 0.30 |
| 20 input validation | 0.00 | 0.30 | 0.07 |
| 89 SQLi / 78 OS injection / 94 code injection / 863 | ≈0 | 0.02–0.42 | ≈0 |

**What it confirms:**
- Textbook sinks (89, 78) are handled.
- Output/context neutralisation (79, 117) and credential storage (522) are not. CWE-522 stays
  around 0.3–0.5 even when the prompt names it, which suggests missing knowledge rather than
  inattention.

This is consistent with CWE-bench on XSS (79), and only weakly informative for repair.

## 4b. Vulnerability repair benchmarks (beyond CWE-bench)

| Source | Task | Per-class data | DeepSeek? |
|---|---|---|---|
| CodeRover-S (arXiv 2411.03346) | 588 ARVO C/C++ bugs, GPT-4o | **yes**, per CWE (Table 1) | no |
| VulnRepairEval (arXiv 2509.03331) | 23 real Python CVEs, a working exploit must fail | per CVE (Table 6), grouped by us | **R1 17%, V3 13%** |
| PatchBench (arXiv 2609.04075) | 213 ARVO tasks with the fix outside the crash stack | no per-CWE | no |
| AutoPatchBench (Meta), SEC-bench, CyberGym-E2E, CVE-Bench (NAACL 2025) | C/C++ crash repair / multi-language CVE repair | no per-CWE | no |
| CWE-bench **v0** (Sep 2026) | 100 tasks, older verifiers | per category and per CWE | DeepSeek **V4** Flash |

**Per-class numbers worth keeping:**
- **Memory safety** (CodeRover-S, GPT-4o; n = tasks):
  - **hard:** use-after-free 416 at 35% (55), uninitialised variable 457 at 34% (47), NULL dereference 476 at 40% (105);
  - **easier:** out-of-bounds read 125 at 90% (20), heap overflow 122 at 69% (67), stack overflow 121 at 57% (244).

  These are unmapped in OWASP 2025 except 476 (A10).
- **Real Python CVEs** (VulnRepairEval, our grouping; n = CVEs):
  - no model fixed ReDoS (3), XSS (2), path traversal (3), DoS (2), protocol/request smuggling (2) or crypto-auth (1);
  - DeepSeek R1 fixed 2 of 3 unsafe-YAML deserialisation.
- **Stated across sources:** localisation is the main failure. A fix that belongs away from the
  crash or symptom site is the dominant cause. PatchBench: 64% of agent patches stay on the
  stack trace even when the real fix is elsewhere. VulnRepairEval: about 60–78% of failures are
  localisation. Multi-site and design-level fixes are harder.

**Agreement and disagreement:**
- **Hard across ≥ 2 sources:** integrity/authenticity (345, 494), deserialisation (502),
  session and auth logic (613, 307), race conditions (362), request smuggling (444), and
  context-dependent memory bugs (416, 457).
- **Easy across ≥ 2 sources:** single-sink injection (89 SQLi, 78 OS command), SSRF (918),
  weak crypto parameters (916, 330), and bounds-check overflows (125, 122).
- **Disagreement on path traversal (22) and XSS (79):** saturated or easy in CWE-bench and
  BaxBench, yet unfixed by every model on real Python CVEs (VulnRepairEval). A CWE label is a
  weaker predictor than the fix's shape.

### More repair evidence (second pass)

- **LiveCVEBench / CVE-Factory (arXiv 2602.03012, 2026, agentic).**
  - **Setup:** 190 reproduced real CVEs, 14 languages, 74 CWEs, with **DeepSeek V3.1 and V3.2**
    among the models (overall about 21–24%; best Opus 4.5 at 42%).
  - **Per CWE (prose only, pooled across models):** code injection **94 at 10.8%** (hardest),
    path traversal 22 at 17.9%, XSS 79 at 25%, access control at 27%, OS command injection
    78 at 46.6% (easiest).
  - **Language:** the same CWE swings by language (SSRF 918: 85% in Python, 0% in PHP), but after
    adjusting for CWE mix the authors call language "second-order".
- **Memory bugs, three studies:**
  - **use-after-free 416** is the hardest class in CodeRover-S (35%) and PatchAgent (temporal
    bugs lowest), and fails under every model in SAN2PATCH (0/2);
  - **NULL dereference and numeric bugs** are easy when a crash log is given: "resolved with a
    simple if-check".
- **Java (Vul4J, Gemini, arXiv 2603.10072):** input validation **20 at 0%**, XSS 17%, path
  traversal 20%, XXE 40%, infinite loop 45%. Quote: "code complexity does not predict
  difficulty; vulnerability semantics does".
- **Exact-match studies** (arXiv 2508.03470): auth 287 and 306 look easy, but this grades
  likeness to the developer's patch, not whether the exploit is blocked. Low weight.

### Abstract classes, injected variants and LLM-in-the-loop bugs (third pass)

- **The more abstract the CWE, the harder the fix.** CWEFT (ESEM 2026, LIPIcs vol. 394 art.
  78; Java Vul4J, 42 CVEs, 504 patches, Claude Sonnet 4.5 / GPT-5 / Gemini 2.5 Pro):
  - correct (exploit test and all regression tests pass) for **CWE-20 input validation: 3.1%**
    (n = 96 cells);
  - **CWE-264, 284 and 269 access control/permissions: 0%**;
  - path traversal 22: 20%, XSS 79: 15%, XXE 611 and deserialisation 502: 25%.

  Quote: "repair rate tracks how concrete the vulnerability class is … a broad class such as
  CWE-20 names a symptom with no single repair shape to retrieve". Gemini Flash on Vul4J agrees:
  CWE-20 at 0%.
- **Injected variants are hard for every model.** Garg et al. (arXiv 2511.23408; Java; 14
  LLMs incl. a DeepSeek R1 distill): real CVEs are fixed up to 47%, but **injected
  "artificial" variants only 0–20%**. The injected CWE-74, 532 and 611 variants were fixed by no
  model. This independently supports our sibling-injection approach. The same study: log leaks
  (CWE-532) 0/14 on the real CVE, and XSS 0/28.
- **LLM-in-the-loop (LiL) vulnerabilities** (arXiv 2605.28893): bugs where an app executes or
  renders LLM output.
  - **Overall:** about 26% fixed on average, 10–16 points below other vulnerabilities.
  - **DeepSeek-V4-Pro** (OpenHands) fixes 41% of LiL bugs but **0/4 "model output rendering"**,
    and 2/7 generated-query and 1/7 agent-action bugs.
  - **This is a source class the screener doesn't target yet** (LangChain-style frameworks,
    agent tools, LLM output rendered as HTML or executed as SQL/code).

### The strongest predictor is the fix's shape, not its CWE (PatchEval, arXiv 2511.11019)

DeepSeek R1 and V3 are among the models (with a location oracle they fix 44 and 41 of 230).
Average repaired per group:

| Fix touches | Repaired / group | Rate |
|---|---|---|
| 1 file | 41.5 / 202 | 20.5% |
| 2 files | 1.3 / 21 | 6% |
| 3+ files | 0 | 0% |
| 1 hunk | 30.4 / 120 | 25% |
| 2 hunks | 10.6 / 69 | 15% |
| 3+ hunks | ≈0 | ≈0% |
| 1–5 lines | 19.2 / 59 | 33% |
| 20–50 lines | 4.6 / 46 | 10% |
| 50+ lines | 0.4 / 19 | 2% |

**Other sources agree:**
- PatchBench: 64% of agent patches stay on the crash trace when the fix is elsewhere.
- VulnResolver: SEC-bench Full has more hunks and lines and a lower resolve rate.
- Pearce et al.: the failures "need large code changes".
- Java study: the size of the human patch correlates with failure (ρ = −0.33).

**Stability of the category ranking** (CWE-bench v0 → v1, same benchmark, rescored with new
verifiers):

| | A01 | A06 | A07 | A08 |
|---|---|---|---|---|
| DeepSeek, v0 | 12 | 19 | 14 | 19 |
| DeepSeek, v1 | 65 | 42 | 58 | 39 |

- **Only A08 and A06 are low in both versions,** so the category ranking is only trustworthy
  at the extremes.
- **The authors agree:** "the verifiers moved more than the models".

## 5. Our own results (both models; 19 tasks)

| Category (tasks touching it) | DeepSeek solved | MiMo solved |
|---|---|---|
| A01 (12) | 11 | 10 |
| A07 (8) | 8 | 7 |
| A06 (4) | 4 | 3 |
| A04 (3) | 3 | 2 |
| A08 (2) | 2 | 1 |
| A05 (2) | 2 | 2 |
| A02 (1) | 1 | 0 |
| unmapped (4) | 4 | 4 |

- **Our failures are all in stacked tasks spanning several categories:** actualbudget,
  stigmem (MiMo) and jackson-databind-sib (DeepSeek). The per-category counts therefore overlap
  and can't attribute a failure to one category.
- **The one robust agreement with CWE-bench:** A01 is mostly solved by both models.
- **MiMo:** this is the only evidence that exists for MiMo, and it is thin.

## 6. Screener change: APPLIED 2026-10-16 as `sourcer/weights.json` v2

**What changed:**
- `osv_sourcer.py` now reads every point value from `weights.json`: S1–S7, the low signals,
  the fetch-queue prescore, the OWASP map and the per-CWE lists.
- The v1 reader rubric (never read by code) is kept in `weights.v1.json`.
- The pre-change index is in `index/candidates.before-weights-v2.sqlite`.

**Effect on the 1,462 candidates:**
- **Agreement with the v1 ranking:** 8 of the top 20, 24 of the top 50, 65 of the top 100.
- **"Favoured" candidates:** down from 857 to 420.
- **Top-50 categories:** v1 was dominated by A01 (21 of 50). v2 is spread across A05 (12),
  A06 (11), A01 (8), A08 (7) and unmapped (7).

**Retro-check against our own trials: inconclusive.**
- 3 easy tasks moved down: jackson-databind #6 → #84, async-http-client #74 → #189,
  rclone #171 → #263.
- 2 easy tasks moved up: russh #235 → #27, webob #346 → #83.

**LLM detector:** an "LLM-in-the-loop" bonus (+2) applies only when the summary says model
output drives the action. That matches 4 candidates. 110 other LLM-app bugs get a 0-point
"ecosystem" label.

The original proposal follows.

Replace today's yes/no "+3 if in a favoured class" with three parts. The weights are
deliberately modest, because two findings say the CWE label is a weaker predictor than the
fix's shape. The main signals stay: S1 multi-site (injectability), S2 symptom–fix disparity
(localisation), S3 ineffective defence, and S6 fix shape. These are different things; see
section 7.

1. **Category points.** These are confident only at the extremes, which are stable across
   CWE-bench v0 and v1:

   | Category | Points |
   |---|---|
   | A08, A06 | +2 |
   | A07, A10, A05, A09, A02, A03 | +1 |
   | A01, A04 | 0 |
   | unmapped | +1 (neutral, unknown) |

2. **CWE adjustment**, where evidence exists for that CWE:

   | Condition | Adjustment |
   |---|---|
   | hard across ≥ 2 sources (345, 494, 502, 613, 307, 362, 444, 416, 457, 20, 532) | +2 |
   | the advisory's CWEs are **only** broad/abstract ones (20, 284, 264, 269, 693, 707) | +1 (abstract classes are repaired least; today the sourcer just skips them when naming) |
   | LLM-in-the-loop bug (app executes or renders model output) | +2 (new: needs a detector, e.g. package is an LLM framework or the advisory mentions prompts/LLM output) |
   | CWE-bench: DeepSeek ≤ 25 and field mean ≤ 50 | +1 |
   | CWE-bench: DeepSeek-specific weak spot (DeepSeek ≤ 25, field > 50) | +1 |
   | saturated in CWE-bench (mean ≥ 90 and DeepSeek 100) **and** not contradicted elsewhere (916, 330, 470, 434, 285, 287, 1104, 319) | −2 |
   | easy across ≥ 2 repair sources (78 OS command, 89 SQLi) | −1 |
   | 22 path traversal, 79 XSS, 94 code injection, 918 SSRF | 0 (sources disagree: easy in CWE-bench, hard on real CVEs or language-dependent) |

   A candidate with several CWEs takes its highest value.

2b. **Weight fix shape more.** This is the strongest predictor found anywhere. S6 already
    rewards 3+ far-apart hunks (+2) and penalises a single compact hunk (−3). PatchEval suggests:

    | Upstream fix touches | Points |
    |---|---|
    | 2+ files | +2 (rate drops from 20% to 6%, and 0% at 3+) |
    | 3+ hunks | +2 (≈0% repaired) |
    | 50+ changed source lines | +1 |

    S1 and S6 measure different things (one decision repeated vs fix size), but the same hunks
    feed both: a check added at 3 sites is also a 3-hunk fix. So their combined points are
    capped.

3. **Reconcile the code and `weights.json`:**
   - the code's class list and `weights.json`'s class names currently don't match;
   - `weights.json` is not read by any code.

   Either wire the file in, or retire it and keep weights in code.

**Not yet settled:**
- **MiMo:** its weights wait for more of our own runs; no MiMo data is published anywhere.
- **PatchEval and Vul4J:** a direct repair-research pass covering these is still running and
  may refine the CWE list.

## 7. Three different signals: multi-site, symptom–fix disparity, fix shape (2026-10-16)

They were blurred in earlier drafts. They are different properties, and the research supports
them differently.

| Signal | Property | Why it matters | Measured today |
|---|---|---|---|
| S1 multi-site | the same trust decision enforced at several independent sites | **injectability**: siblings can only be planted where the decision recurs (a single choke point cannot host them; async-sib and tomcat-sib were abandoned for this). Also difficulty: closing 2 of 3 sites scores zero (CWE-bench). | well: "the same new check added at N sites" in the upstream fix |
| S2 symptom–fix disparity | the bug shows in one place but the fix belongs in another function, file or layer | **localisation**, the dominant repair failure in every source: PatchBench (64% of patches stay on the crash trace), VulnRepairEval (60–78% of failures), CWE-bench ("fix where tokens are created, not where they are cancelled") | **weakly**: only from advisory wording (+2), which rarely fires |
| S6 fix shape | files, hunks and lines the fix touches | PatchEval's size effect | well: from the diff |

**How they relate:**
- **They can be independent.** A 3-hunk fix may be one check repeated (S1 and S6) or three
  unrelated edits (S6 only). A one-line fix may sit far from the symptom (S2 only).
- **S1 sees only the sites the upstream fix touched.** The best injection bases are where the
  same decision recurs at sites the fix did not cover. Finding those needs a search of the
  repository at the vulnerable commit (other call sites of the guarded function). That is a
  heavier, later step.

### Proposed: a computed S2 (not built yet)

1. **Where the bug shows:** extract the identifiers the advisory names (function and method
   names, file paths, HTTP endpoints, CLI commands) from its summary and details. They would go
   into `adv_signals`, a JSON column, so no schema change; `resignal` rebuilds it from the
   dumps.
2. **Where the fix lands:** record the changed files and the function names from the diff's
   hunk headers. These would go into the commit's `shape` JSON, again no schema change;
   `remetrics` rebuilds it from the cached patches.
3. **The signal:**

   | Case | Points |
   |---|---|
   | the advisory names a location and the fix touches none of it | +3 |
   | the fix lands exactly on the named location | −1 (easy to localise) |
   | the advisory names no location | 0 (unknown) |

4. **Validate before trusting it,** on our 19 built tasks, where we know both the symptom and
   the fix location.

## 8. Last repair sources (SEC-bench per class, PatchBench, Beyond Resolution Rates)

- **SEC-bench (C/C++, 200 CVEs).** Per-class rates were computed by our research agent from the
  published per-run results; the paper itself has no per-class table.
  - **Use-after-free** is the hardest large class in every run, 16–30 points below the overall
    rate.
  - **Double-free and bad-free** are near 0 (n = 3–5).
  - **Out-of-bounds read (125) and NULL dereference (476)** are the easiest.
  - **Multi-file fixes are only modestly harder:** 75% vs 63% for the best run.
  - 40 of 300 tasks were never solved, mostly heap overflows and use-after-free.
- **PatchBench (213 C/C++ tasks with the fix off the crash stack).**
  - The most common failure is "agents guard the symptom with incomplete local checks".
  - 64% of agent patches still edit crash-stack functions when the real fix is elsewhere.
  - "Budget is not what holds the agents back."
  - PoC-only grading inflates solve rates 1.83×.
- **Beyond Resolution Rates (SWE-bench Verified, general bugs, not security).**
  - Among the 55 never-solved tasks, 12 need simple patches.
  - Their patch complexity is "statistically indistinguishable" from always-solved tasks.
  - Agents "intervene at the wrong architectural layer" in 10 of 12, even though the best agent
    found the right file in all 12.

**What this changes:** localisation and wrong layer are the most consistent predictor across
sources. Fix size is source-dependent. Summary point 1 was corrected accordingly.
