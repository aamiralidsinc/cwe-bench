<!-- Verbatim final report of a research sub-agent (id a25ce68629b0e534c), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

# Per-CWE evidence on how well LLMs and agents repair vulnerabilities (as of 2026-10-16)

Numbers labelled "stated" are copied from the paper or the authors' artifact. Numbers labelled "MY COMPUTATION" are my own, and the method is given each time.

**Main finding:** no source in this set reports a per-CWE result for Xiaomi MiMo, and nothing turned up for MiMo in any search. DeepSeek results exist, but only in these forms:
- **Source 1:** per LLM-in-the-Loop category, not per CWE.
- **Source 6:** per CVE with a CWE label, from which I computed a per-CWE view.
- **Sources 7, 8 and 9:** overall results only, with no per-CWE data.

---

## 1. "LiL vulnerabilities" paper — arXiv 2605.28893v2

"Towards Demystifying and Repairing LLM-in-the-Loop Vulnerabilities", Ma et al. URL: https://arxiv.org/html/2605.28893v2

- **Task:** repair of real CVEs. LiLCVE has 41 LiL (LLM-in-the-Loop) CVEs and 75 LLM-ecosystem CVEs, 116 in total.
  - The paper does not state the language. It says "Agentless and AutoCodeRover are evaluated only on Python projects". Those two tools use a 50 / 35 denominator instead of 75 / 41.
  - Grading uses a security test plus a functionality test.
- **Setup:** 5 agents (OpenHands, SWE-agent, Aider, AutoCodeRover, Agentless) × 4 models (GPT-4o, GPT-5.2-Codex, **DeepSeek-V4-Pro**, MiniMax-M2.5), giving 20 configurations. There is no MiMo.
- **Per-class results:** Table III, Section IV-B1, Pass@1. The classes are LiL categories, not CWEs: there is no per-CWE repair table.
  - CWE make-up is only in Figure 2, which is an image. The text says CWE-94, -89, -74 and -77 make up 65.9% of LiL vulnerabilities.
  - Categories: c1 Generated Code/Expression Execution (n=20), c2 Generated Query Execution (n=7), c3 Agent/Tool Action (n=7), c4 Model Output Rendering (n=4), c5 Output Parsing/Dispatch (n=3).

DeepSeek-V4-Pro rows, copied from Table III:

| Agent + DeepSeek-V4-Pro | Eco (n=75) | LiL all (n=41) | c1 | c2 | c3 | c4 | c5 |
|---|---|---|---|---|---|---|---|
| OpenHands | 60.00% (45/75) | 41.46% (17/41) | 55.00% (11/20) | 28.57% (2/7) | 14.29% (1/7) | 0.00% (0/4) | 100.00% (3/3) |
| SWE-agent | 54.67% (41/75) | 48.78% (20/41) | 60.00% (12/20) | 28.57% (2/7) | 28.57% (2/7) | 25.00% (1/4) | 66.67% (2/3) |
| Aider | 28.00% (21/75) | 9.76% (4/41) | 40.00% (8/20) | 0.00% (0/7) | 14.29% (1/7) | 0.00% (0/4) | 66.67% (2/3) |
| AutoCodeRover | 34.00% (17/50) | 28.57% (10/35) | 35.00% (7/20) | 0.00% (0/6) | 0.00% (0/4) | 50.00% (1/2) | 66.67% (2/3) |
| Agentless | 40.00% (20/50) | 28.57% (10/35) | 40.00% (8/20) | 16.67% (1/6) | 0.00% (0/4) | 0.00% (0/2) | 33.33% (1/3) |

Other rows, all copied from Table III:

| Configuration | Eco | LiL all | c1 | c4 |
|---|---|---|---|---|
| OpenHands + GPT-5.2-Codex | 56.00% (42/75) | 53.66% (22/41) | 75.00% (15/20) | 25.00% (1/4) |
| OpenHands + GPT-4o | 17.33% (13/75) | 7.32% (3/41) | 10.00% (2/20) | 0.00% |

- MiniMax-M2.5 with OpenHands: Eco 52.00%, LiL 29.27%.
- I can provide the full 20-row table if needed.

**Stated findings on hard and easy classes:**
- "three categories, Generated Query Execution, Agent Action, and Model Output Rendering … frequently receive 0% repair success rates"
- "16 out of 20 configurations achieving a 0% Pass@1 in at least one category"
- "C4 is especially challenging, receiving 0.00% Pass@1 in 15 out of 20 situations"
- "C1 is relatively more tractable"
- "C2–C4 are consistently harder, likely because their repair targets are less localized"
- "Existing methods can fix 25.8% (on average) of LiL vulnerabilities, which is 10.8% and 15.5% lower than fixing LLM-ecosystem and conventional software vulnerabilities"

**Difficulty factors:**
- Table V (patch size):

| Group | Median lines | Mean lines | Median hunks | Median files |
|---|---|---|---|---|
| LiLCVE | 43.0 | 56.4 | 3 | 1 |
| LLM-ecosystem | 14.0 | 28.8 | 2 | 1 |

- Quote: "the additional complexity mainly arises from a larger modification scope within the affected files".
- Table IV is a logistic regression. The odds ratio for being a LiL vulnerability is 0.578 (95% CI 0.350–0.957, p=0.033). It holds when controlling for agent (0.567), language (0.586), CVSS (0.557) and year (0.595).
- Quote: "the main repair challenge is therefore boundary completeness rather than simple vulnerability recognition".
- Table VII gives failure causes on LiL vulnerabilities. "Security Only" failures are the largest share, 27–44% per agent; for example SWE-agent 44.4% (48/108).

**Problems in the paper:**
- The text swaps the 60.00 / 41.46 values for OpenHands + DeepSeek. Table III shows 60.00% is the ecosystem value.
- The abstract says 15.5% / 30.3% for critical severity, while Section II-C says 28.8% / 35.1%.

---

## 2. Vul4Py — arXiv 2608.00692

Bui, Zhang, Thung, … Lo. URL: https://arxiv.org/html/2608.00692. Repo: https://github.com/tabudz/vul4py

- **Task:** repair of real CVEs in Python. 100 vulnerabilities from 60 projects, covering 60 CWEs, 2017–2025.
  - Each task has two oracles: an exploit test and the project's pytest suite.
- **Models:** APPATCH (Claude Sonnet 4), GPT-4o direct, Claude Sonnet 4 direct, and OpenHands, Trae Agent and SWE-agent (all on Claude Sonnet 4). There is no DeepSeek and no MiMo.
- **Results (Table 2):** given as exploit-pass / plausible / correct.
  - OpenHands 51/43/41
  - Trae 33/30/29
  - SWE-agent 27/24/22
  - Claude Sonnet 4 5/5/4
  - APPATCH 3/2/2
  - GPT-4o 0/0/0
- **Per-CWE:** none published. The CWE distribution is only in prose: CWE-770 and CWE-400 have 8 each, and 42 CWEs have exactly one instance.
- **Difficulty factors:** none measured. Patch-size statistics (median 65 lines, mean 103, maximum 584) are not linked to success.
- **Repo check:** `dataset/vul4py.csv` holds only vuln_id, repo_url and fix_commit. `results/` contains only `.gitkeep`, so there is no per-instance data to compute from.

---

## 3. ESEM 2026 study — the ID given does not match

- **arXiv 2608.18280 is not a vulnerability-repair paper.** It is "What Makes Software Issue Resolution Tasks Difficult for Agents?" (Al-Haque & Johnson, ESEM 2026). URL: https://arxiv.org/html/2608.18280
  - It uses CoderForge-Preview: 45,769 SWE-Smith and SWE-Rebench tasks, mostly Python, with Qwen3-Coder-480B on OpenHands. There is no DeepSeek or MiMo.
  - It does not mention security, CWEs or vulnerabilities. There is no per-CWE data.
  - **Difficulty factors (Tables 2, 6 and 7):**
    - XGBoost reaches AUC 0.863. Patch features alone give AUC 0.846, repository features alone 0.839, prompt features alone 0.599.
    - Top SHAP features are `patch_lines_deleted` (mean |SHAP| 0.406), `patch_num_hunks` and `patch_hunk_gap_mean`. `repo_top_level_dir_count` is 4th.
    - Quote: "largely driven by patch fragmentation and repository scale"
    - Quote: "Patch complexity and repository structure together account for virtually all of the predictable variance"
- **The ESEM 2026 vulnerability-repair paper is likely this one:** "CWEFT: CWE-Aware Evaluation of Free-Text vs. Typed Prompts", Carbonell & Koyuncu, LIPIcs ESEM 2026 article 78. I found no arXiv ID.
  - PDF: https://drops.dagstuhl.de/storage/00lipics/lipics-vol394-esem2026/LIPIcs.ESEM.2026.78/LIPIcs.ESEM.2026.78.pdf
  - Replication package with all 504 per-cell outcomes: https://doi.org/10.5281/zenodo.21672348
  - **Task:** repair of real CVEs in Java (Vul4J), single-shot, whole-file output. 42 vulnerabilities whose human patch touches one file, across 15 CWEs.
  - **Design:** 4 prompt conditions × 3 models (Claude Sonnet 4.5, GPT-5, Gemini 2.5 Pro) = 504 patches. There is no DeepSeek and no MiMo.
  - **Correct means L3:** the proof-of-vulnerability (PoV) test passes and all regression tests pass.
  - **Overall:** 16.5% correct, 22.6% pass the PoV, 77.2% compile.
    - By model: Gemini 22.0%, Claude 14.3%, GPT-5 13.1%.
    - By prompt: baseline C1 12.7%, CWE named (C2) 19.8% (p=0.049), C3a and C3b both 16.7%.

Table 6 (Section 4, RQ4), L3 rate by CWE. n is the number of cells (vulnerabilities × 12), pooled over all 3 models and 4 conditions:

| CWE | n cells | L3 % |
|---|---|---|
| CWE-287 Improper authentication | 24 | 37.5 |
| CWE-611 XXE | 48 | 25.0 |
| CWE-502 Deserialization | 24 | 25.0 |
| CWE-835 Infinite loop | 84 | 21.4 |
| CWE-22 Path traversal | 60 | 20.0 |
| CWE-79 XSS | 60 | 15.0 |
| CWE-20 Improper input validation | 96 | 3.1 |
| CWE-264 Permissions / access control | 24 | 0.0 |
| CWE-74 Injection (single vuln) | 12 | 91.7 |
| CWE-532 Sensitive info in log (single) | 12 | 16.7 |
| CWE-77 Command injection (single) | 12 | 8.3 |
| CWE-284, CWE-310, CWE-269, CWE-19 (single each) | 12 each | 0.0 |

- No per-model per-CWE split is published; it is only in the Zenodo package, which I did not download.
- **Quotes:**
  - "repair rate tracks how concrete the vulnerability class is, falling to 3.1% for improper input validation"
  - "Broad, abstract classes are repaired rarely or never"
  - "a broad class such as CWE-20 names a symptom with no single repair shape to retrieve"
  - "the 91.7% for CWE-74 … comes from a single injection bug"
- **Fix-size analysis:** none. The study is restricted to single-file human patches by design.

---

## 4. Vul4J / VJBench / Java CVE studies

### 4a. Wu et al., ISSTA 2023 — arXiv 2305.18607

URLs: https://arxiv.org/html/2305.18607v2 and https://arxiv.org/pdf/2305.18607v2

- **Task:** repair of real CVEs in Java. 50 single-hunk vulnerabilities: 35 from Vul4J and 15 from VJBench. VJBench-trans adds 150 transformed variants.
- **Models:**
  - Codex
  - CodeT5, CodeGen, PLBART, InCoder, each as-is and fine-tuned
  - APR tools CURE, Recoder, RewardRepair, KNOD
  - There is no DeepSeek and no MiMo.
- **Table 4 (Section 6.1), correct / plausible out of 50:**
  - Codex 10.2 / 15.5 (20.4%)
  - FT-InCoder 9 / 13
  - FT-CodeGen 8 / 12
  - InCoder 5 / 6
  - FT-CodeT5 5 / 11
  - FT-PLBART 4 / 9
  - CodeT5, CodeGen and PLBART 2 each
  - RewardRepair 2
  - CURE, Recoder and KNOD 1 each
- **Table 5 (Section 6.2):** the 16 vulnerabilities fixed by at least one of 13 tools, with CWE labels.
  - Column totals: Codex 15, CodeT5 2, CodeGen 2, PLBART 2, InCoder 5, FT-CodeT5 5, FT-CodeGen 8, FT-PLBART 4, FT-InCoder 9, CURE 1, Recoder 1, RewardRepair 2, KNOD 1.
  - The checkmarks are glyphs and cannot be reliably mapped to columns from either the HTML or the PDF text, except for Codex, which the text confirms.
  - The fixed vulnerabilities and their CWEs (copied):

| Vuln | CWE |
|---|---|
| Vul4J-1 | 20 |
| Vul4J-4, Vul4J-5, Vul4J-19, Vul4J-20 | unk |
| Vul4J-12 | 835 |
| Vul4J-25 | "39" (as printed, labelled XSS) |
| Vul4J-39 | 200 |
| Vul4J-47 | 611 |
| Vul4J-50, Vul4J-59 | 79 |
| Vul4J-73 | 522 |
| Halo-1 | 22 |
| Jenkins-2, Jenkins-3 | 200 |
| Ratpack-1 | 74 |

  - Codex fixed all of these except Vul4J-39.
  - **MY COMPUTATION** (count of checkmarks per row from the PDF text, ±1 uncertainty because rows sum to 58 against column totals of 57): Ratpack-1 (CWE-74) 7 tools; Vul4J-12 (835), Vul4J-39 (200), Jenkins-2 (200) and Jenkins-3 (200) 6 each; the rest 1–4.
- **Quotes:**
  - "the nine LLMs and four APR techniques fix none of the six new CWE types that VJBench adds" (CWE-172, -325, -347, -444, -668, -1295)
  - "Codex fixes Vul4J-47, but none of the LLMs and APR techniques fixes the additional Quartz-1 and Retrofit-1" (both CWE-611)
  - Most-fixed cases (6–7 of 13 tools) need only a deleted `if` or a `while`→`if` change: "The simplicity of these patches are evident from the number of models that can fix them."
  - "except Codex, other LLMs and fine-tuned LLMs only fix vulnerabilities that require simple modifications such as deleting statements or replacing variable/method names"
- **Size:** single-hunk only by design. VJBench's 27 multi-hunk vulnerabilities were excluded.
- **Transformations (Table 6):** renaming plus code-structure changes drop Codex from 10.2 to 8.7, and FT-InCoder from 9 to 4.

### 4b. "Why LLMs Fail", Al-Maamari, arXiv 2603.10072

URLs: https://arxiv.org/html/2603.10072v1 and repo https://github.com/AmeerAlmaamari/LLM-Security-Patches-Analysis

- **Task:** repair of real CVEs in Java (Vul4J). 64 vulnerabilities × 5 samples at temperature 0.7 = 319 patches, across 21 CWE categories.
- **Model:** Gemini Flash. The paper says "2.0 Flash" in the introduction and "3.0 Flash" in Section 4.2. The repo config is `google/gemini-3-flash-preview`. There is no DeepSeek and no MiMo.
- **Overall:** 24.8% of patches are fully correct (79/319). 51.4% fail both security and functionality.
- **Table 5 (Section 5.3, RQ3), CWEs with n≥20 patches:**

| CWE | n patches | Compile % | SRS | Fix % |
|---|---|---|---|---|
| CWE-835 | 40 | 100 | 0.725 | 45 |
| CWE-20 | 40 | 95 | 0.469 | 0 |
| CWE-79 | 30 | 83 | 0.489 | 17 |
| CWE-611 | 25 | 80 | 0.516 | 40 |
| CWE-22 | 25 | 72 | 0.458 | 20 |
| CWE-264 | 20 | 100 | 0.573 | 15 |

- **What "Fix %" means:** the paper does not define it. The repo's `scripts/14_difficulty_predictors.py` computes it as `security_fix_rate` (PoV/security pass ÷ patches), not full correctness.
- **Remaining CWEs:** these come from the authors' artifact, not the paper. File: `results/analysis/difficulty_predictors.csv`. Columns are n patches / mean SRS / compile rate / security fix rate:
  - CWE-200: 5 / 0.0 / 0% / 0%
  - CWE-863: 5 / 0.397 / 80% / 0%
  - CWE-352: 5 / 0.40 / 40% / 40%
  - "Not Mapping": 49 / 0.408 / 71.43% / 20.41%
  - CWE-78: 5 / 0.470 / 100% / 0%
  - CWE-532: 5 / 0.483 / 100% / 0%
  - CWE-284: 5 / 0.488 / 100% / 0%
  - CWE-269: 5 / 0.491 / 100% / 0%
  - CWE-19: 5 / 0.498 / 100% / 0%
  - CWE-77: 5 / 0.500 / 100% / 0%
  - CWE-287: 10 / 0.65 / 100% / 30%
  - CWE-502: 15 / 0.663 / 100% / 33.33%
  - CWE-310: 5 / 0.899 / 100% / 80%
  - CWE-74: 10 / 1.000 / 100% / 100%
  - CWE-918: 5 / 1.0 / 100% / 100%
- **Quotes:**
  - "CWE-20 (Input Validation) achieves 0% fix rate despite high functionality"
  - "input validation requires domain-specific knowledge about what constitutes valid input"
  - "CWE-835 (Infinite Loop) achieves 45% fix rate with near-perfect functionality preservation"
- **Size:** human patch size has Spearman ρ = −0.331 (p=0.008) with SRS (the paper's Security Repair Score), but Pearson r = 0.022 is not significant. Lines of code, cyclomatic complexity and number of files are not significant (number of files ρ = 0.088). Quote: "vulnerabilities requiring larger human patches are systematically harder … but the effect is not proportional".

### 4c. Garg, Khan, Degiovanni, Tang (SAC 2026 poster, extended) — arXiv 2511.23408

URL: https://arxiv.org/pdf/2511.23408

- **Task:** Java (Vul4J). 15 real CVEs plus 41 injected "artificial" variants. One-shot, function-only input. Success = compiles and passes the PoV.
- **Models:** 14 LLMs, including **"DeepSeekR1 Qwen 32B"** as written in the paper (most likely the R1 distill), GPT-3.5/4/4o variants, LLaMA 3.1/3.3 70B and Mistral variants. There is no MiMo.
- **Table 3:**
  - DeepSeekR1 Qwen 32B: 14/56 (25.00%); real 6/15 (40.00%); artificial 8/41 (19.51%)
  - Mistral 8x7B: 14 (25.00%); real 7/15 (46.67%); artificial 7/41
  - GPT-4: real 6/15
  - GPT-4o: real 5/15
- **Per-CWE:** Table 1 gives CVE→CWE and Table 2 gives a per-CVE × model checkmark grid. There is no per-CWE table.
- **MY COMPUTATION** for real CVEs: model successes out of 14 models per CVE, grouped by CWE. My counts reproduce Table 3's column sums exactly (real 70, artificial 43).

| CWE | real CVEs (n) | model-successes / attempts | DeepSeekR1-Qwen-32B |
|---|---|---|---|
| CWE-310 (CVE-2013-5960) | 1 | 14/14 | ✓ |
| CWE-22 (CVE-2018-1000850) | 1 | 13/14 | ✓ |
| CWE-20 (CVE-2018-1000531) | 1 | 10/14 | ✓ |
| CWE-74 (CVE-2014-4172, CVE-2018-1000854) | 2 | 14/28 (0 + 14) | 1 of 2 |
| CWE-835 (CVE-2018-11771, -17201, CVE-2019-12402) | 3 | 12/42 (1 + 11 + 0) | 1 of 3 |
| CWE-284 (CVE-2016-6802) | 1 | 4/14 | ✗ |
| CWE-noinfo (APACHE-COMMONS-001, HTTPCLIENT-1803) | 2 | 3/28 | 1 of 2 |
| CWE-79 (CVE-2016-10006, -2162) | 2 | 0/28 | ✗ |
| CWE-611 (CVE-2017-5662) | 1 | 0/14 | ✗ |
| CWE-532 (CVE-2018-1000089) | 1 | 0/14 | ✗ |

- Artificial variants: all 10 CWE-74 variants of CVE-2014-4172, all 7 CWE-532 variants and all 6 CWE-611 variants got 0 fixes from every model.
- **Quotes:**
  - "LLMs handle single-location fixes quite well. However, their success rate drops when a vulnerability demands several interdependent edits scattered across the codebase."
  - On CVE-2017-5662 (XXE), the fix also needs a build-file dependency upgrade: "None of the LLMs produced both edits".

### 4d. Wang et al., "On the Evaluation of LLMs in Multilingual Vulnerability Repair" — arXiv 2508.03470 (TOSEM; ICSE 2026 journal-first)

URLs: https://arxiv.org/pdf/2508.03470v1 and https://arxiv.org/html/2508.03470v1

- **Task:** REEF function pairs in 7 languages; Java has 343 test pairs. The metric is **exact match to the reference fix, not tests**.
- **Models:** GPT-4o (zero-shot, few-shot, instruction-tuned zero-shot, instruction-tuned few-shot), GPT-3.5, Llama 3, Code Llama, **DeepSeek-Coder 6.7B** (and 33B in Section 5.2), plus PLMs and AVR tools. There is no MiMo.
- **Per-CWE:** reported only for GPT-4o with instruction tuning and few shots, and for VulMaster. There is no DeepSeek per-CWE data.
- **Table 6 (Section 4.3), LLM column, all languages pooled, exact match at beam 1:**
  - CWE-287: 93/129 (72.09%)
  - CWE-306: 7/11 (63.64%)
  - CWE-77: 18/38 (47.37%)
  - CWE-362: 5/11 (45.45%)
  - CWE-79: 103/252 (40.87%)
  - CWE-89: 20/64 (31.25%)
  - CWE-352: 16/51 (31.37%)
  - CWE-269: 4/13 (30.77%)
  - CWE-502: 8/27 (29.63%)
  - CWE-20: 28/102 (27.45%)
  - CWE-416: 8/30 (26.67%)
  - CWE-94: 6/23 (26.09%)
  - CWE-476: 14/65 (21.54%)
  - CWE-918: 7/32 (21.88%)
  - CWE-863: 7/33 (21.21%)
  - CWE-22: 17/85 (20.00%)
  - CWE-434: 1/5 (20.00%)
  - CWE-78: 5/27 (18.52%)
  - CWE-119: 5/28 (17.86%)
  - CWE-787: 12/76 (15.79%)
  - CWE-190: 6/49 (12.24%)
  - CWE-798: 1/2 (50.00%)
  - CWE-125: 0/44 (0.00%)
  - CWE-862: 0/4 (0.00%)
  - CWE-276: 0/3 (0.00%)
  - Average: 391/1204 (32.48%)
- **Table 9, GPT-4o worst CWEs:** CWE-125 0% (44), CWE-835 0% (16), CWE-401, -134, -338, -824, -674 0%, CWE-369 5.88%, CWE-617 5.88%, CWE-415 7.69%.
- **Table 8, Java across all techniques:** highest CWE-681 at 40.63%, lowest CWE-1236 at 0.00%.
- **Language:** "Go consistently achieves the best results, while C/C++ shows the relatively weakest performance."

### 4e. Other Java / Vul4J studies

- **Antal et al., EASE 2025 (arXiv 2506.11561):** GPT-4o, 42 Vul4J vulnerabilities. No per-CWE data.
  - The CWE-description prompt gives a 29.4% average versus 37.3% for the CVE description.
  - Quote: the model struggles "when the vulnerable implementation does not support the usually applicable patch pattern (e.g., CWE-611)".
  - URL: https://arxiv.org/abs/2506.11561
- **VRpilot (arXiv 2405.15690):** gpt-3.5 on Vul4J and VJBench. No per-CWE data.
  - Quote: "the complexity of a vulnerable code fix cannot be determined only by the corresponding vulnerability category."
  - URL: https://arxiv.org/html/2405.15690
- **VulKey (arXiv 2605.01769):** Vul4J results only in aggregate (35 single-hunk vulnerabilities). DeepSeek-Coder-V2-Lite is a baseline. Its per-CWE Table 5 is **PrimeVul C/C++, exact match**, for StarCoder versus VulKey only. Example: CWE-416 3/29 → 6/29.
  - URL: https://arxiv.org/html/2605.01769v1
- **Ananbeh, Alnozami, Kim, Automated Software Engineering 33:75 (2026):** 2,362 Java vulnerabilities across 32 CWEs. Paywalled, and I did not verify it.
  - Search snippets say ChatGPT-4 with retrieval-augmented prompting reaches a 76.84% fix rate.
  - Search snippets say the authors report "recurring difficulties … CWE-798 … CWE-23".
  - URL: https://link.springer.com/article/10.1007/s10515-026-00622-z

### Related, not Java: PatchEval — arXiv 2511.11019

URL: https://arxiv.org/html/2511.11019v1

- **Task:** Go, JavaScript and Python. 230 CVEs with a sandbox and tests.
- **Models include Deepseek-R1-0528 and Deepseek-V3-0324.** Table 3 (location oracle given): DeepSeek-R1 44/230, DeepSeek-V3 41/230; best is SWE-agent + Gemini 2.5 at 53. There is no MiMo.
- No per-CWE data.
- **Table 9, repairs averaged over approaches** (average repaired / total, rate is MY COMPUTATION):

| Measure | Bucket | Avg repaired / total | Rate |
|---|---|---|---|
| Files | 1 | 41.5 / 202 | ≈20.5% |
| Files | 2 | 1.3 / 21 | — |
| Files | 3+ | 0 / 7 | 0 |
| Hunks | 1 | 30.4 / 120 | 25.3% |
| Hunks | 2 | 10.6 / 69 | 15.4% |
| Hunks | 3 | 0.6 / 17 | — |
| Hunks | 6+ | 0 / 5 | 0 |
| Lines | 1–5 | 19.2 / 59 | — |
| Lines | 50+ | 0.4 / 19 | — |

- Quote: "the average repair rate for simple CVEs (patches modifying 1–5 lines) is 32.5%, whereas it drops to 7.7% for complex CVEs (patches modifying 20+ lines)".

---

## My inferences, separate from the stated data

1. **CWE labels are a weak predictor of difficulty across studies.**
   - CWE-20 is near 0% in two Vul4J studies: 0% security fix in Gemini Flash and 3.1% L3 in CWEFT.
   - Yet a different CWE-20 CVE was fixed by 10 of 14 models in Garg et al., and CWE-20 scores 27.45% exact match in REEF.
   - CWE-835 is 45% / 21.4% on Vul4J but 0% exact match for GPT-4o on REEF.
   - Per-class n is tiny everywhere (often 1–8 vulnerabilities), so per-CWE rates mostly reflect individual instances. CWEFT says this itself about its singleton classes.
2. **Fix shape is the most consistent signal across sources:** hunks, files, lines, and whether the fix sits at a non-local boundary. It shows up in:
   - PatchEval's hunk and file buckets
   - LiL's larger patches and the "less localized" C2–C4 categories
   - ISSTA'23's finding that simple deletions and replacements are fixed most
   - the Garg et al. XXE case that also needs a build-file change
   - the ESEM issue-resolution SHAP results
3. **Classes that keep showing up as hard to fix:**
   - broad or semantic classes: CWE-20, CWE-264/284/269 access-control and permissions
   - XXE when it needs more than a parser flag
   - CWE-532 log leaks (0% in Garg et al.'s real and artificial cases, and in Gemini's 5 patches)
   - injected or artificial variants, which in Garg et al. drop every model, DeepSeek included, to 0–20%

  Classes that come out easy: one-line canonical fixes such as CWE-310 mode/tag constants, CWE-74 header flags, CWE-287, and single-statement deletions under CWE-200.
4. **DeepSeek:** in LiL, DeepSeek-V4-Pro is mid-to-top of the field (OpenHands LiL 41.46% versus GPT-5.2-Codex 53.66%), but scores 0/4 on Model Output Rendering. In Garg et al., the R1-distill ties for the best total.
5. **Gaps:** no per-CWE results exist for MiMo, and none for DeepSeek on Vul4J, VJBench or Vul4Py, in any source I found.
