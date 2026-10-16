<!-- Verbatim final report of a research sub-agent (id a29a0b5642188c769), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

## Per-CWE results for LLM vulnerability repair: sources not on the skip list

**Method.** I read each paper's arXiv HTML. For three PDFs (PatchAgent, SAN2PATCH, and Wu et al. 2312.05275) I ran pdftotext into the scratchpad and nowhere else.

**Reliability of the numbers.**
- The tables for SAN2PATCH, PatchAgent and 2312.05275 were copied straight from the extracted PDF text.
- The arXiv HTML tables came back through a fetch-and-summarise tool. They look exact, but spot-check them before citing.
- Anything marked **[inference]** is my own calculation, not a stated number.
- I left out CWE-bench 2610.17020 (Gonzalez-Pumariega … Rajani). It appears to be the Collinear CWE-bench, which is on the skip list.

**DeepSeek and MiMo.**
- MiMo: I found no vulnerability-repair study that evaluates it. The only security numbers I saw are Xiaomi's own self-reported offensive scores (CyberGym, ExploitBench).
- DeepSeek: several studies evaluate it (sources 1, 3, 10, 11 and 12), but none gives DeepSeek's success per CWE. In source 1 the per-CWE columns are GPT-4o, VulMaster and CodeT5. In source 3 the per-CWE rates are pooled across all models.

---

### 1. Multilingual repair study: Wang et al., arXiv 2508.03470 (ICSE 2026 journal-first) — the most useful source

**URL:** https://arxiv.org/html/2508.03470v1

**Task**
- Repair of real NVD CVE functions from the REEF dataset (CVEs from 2016–2023).
- Seven languages, 2,142 test function pairs: C 305, C++ 275, C# 47, Go 334, Java 343, JS 484, Py 354.
- Metric: exact match (EM@1) against the developer fix. **This is not test-based.**

**Models**
- Automated repair tools: VulMaster and others.
- Pre-trained models: CodeT5 and others.
- LLMs: **DeepSeek-Coder 6.7B / 33B**, Code Llama, Llama 3, GPT-3.5, GPT-4o.
- Overall EM@1 with instruction tuning plus few-shot (Table 4): DeepSeek-Coder 20.96%, GPT-4o 28.71%. VulMaster 28.94% (Table 3).

**Table 6 — CWE Top 25 (2023).** Columns are CodeT5 / VulMaster / GPT-4o (instruction-tuned, few-shot), shown as count (EM%).

| CWE | n | CodeT5 | VulMaster | GPT-4o |
|---|---|---|---|---|
| 787 | 76 | 11 (14.47) | 12 (15.79) | 12 (15.79) |
| 79 | 252 | 53 (21.03) | 106 (42.06) | 103 (40.87) |
| 89 | 64 | 6 (9.38) | 14 (21.88) | 20 (31.25) |
| 416 | 30 | 4 (13.33) | 8 (26.67) | 8 (26.67) |
| 78 | 27 | 2 (7.41) | 6 (22.22) | 5 (18.52) |
| 20 | 102 | 11 (10.78) | 27 (26.47) | 28 (27.45) |
| 125 | 44 | 0 (0.00) | 2 (4.55) | 0 (0.00) |
| 22 | 85 | 1 (1.18) | 11 (12.94) | 17 (20.00) |
| 352 | 51 | 12 (23.53) | 18 (35.29) | 16 (31.37) |
| 434 | 5 | 0 | 1 (20.00) | 1 (20.00) |
| 862 | 4 | 0 | 0 | 0 |
| 476 | 65 | 5 (7.69) | 12 (18.46) | 14 (21.54) |
| 287 | 129 | 82 (63.57) | 93 (72.09) | 93 (72.09) |
| 190 | 49 | 4 (8.16) | 10 (20.41) | 6 (12.24) |
| 502 | 27 | 5 (18.52) | 11 (40.74) | 8 (29.63) |
| 77 | 38 | 3 (7.89) | 8 (21.05) | 18 (47.37) |
| 119 | 28 | 2 (7.14) | 4 (14.29) | 5 (17.86) |
| 798 | 2 | 0 | 0 | 1 (50.00) |
| 918 | 32 | 2 (6.25) | 7 (21.88) | 7 (21.88) |
| 306 | 11 | 2 (18.18) | 7 (63.64) | 7 (63.64) |
| 362 | 11 | 0 | 5 (45.45) | 5 (45.45) |
| 269 | 13 | 0 | 3 (23.08) | 4 (30.77) |
| 94 | 23 | 2 (8.70) | 3 (13.04) | 6 (26.09) |
| 863 | 33 | 3 (9.09) | 7 (21.21) | 7 (21.21) |
| 276 | 3 | 0 | 0 | 0 |
| **Avg** | **1204** | **210 (17.44)** | **375 (31.15)** | **391 (32.48)** |

**Table 9 — top 10 best and worst CWEs.** The extracted layout was partly garbled, so treat this as approximate.
- GPT-4o best: CWE-287 72.09% (n=129), CWE-306 63.64% (11), CWE-285 53.85% (13), CWE-77 47.37% (38), CWE-362 45.45% (11).
- GPT-4o worst: 0% on CWE-125 (44), CWE-835 (16), CWE-134 (7), CWE-401/338/824/674 (5 each). CWE-369 and CWE-617 5.88% (17 each). CWE-415 7.69% (13).
- VulMaster worst: CWE-125 4.55%, CWE-835 6.25%.

**Table 8 — highest and lowest EM CWE per language (examples)**
- Go: CWE-287 60.25% / CWE-208 0%
- C: CWE-327 31.25% / CWE-121 0%
- Python: CWE-522 45.31% / CWE-1021 0%

**Quotes**
- On CWE-125 and CWE-835: "GPT-4o failed to repair any instances of these vulnerabilities".
- On CWE-835: "among the most frequently occurring CWEs where both GPT-4o and VulMaster perform poorly".
- On language: "Go consistently achieves the best results, while C/C++ shows the relatively weakest performance". LLM medians by language: Go 31.59%, Java 22.59%, JS 18.18%, C# 18.09%, Py 17.94%, C 8.03%, C++ 6.73%.
- On model size: "DeepSeek-Coder (6.7B) achieves a higher EM score of 20.96%, outperforming its 33B counterpart".
- No analysis of patch size.

---

### 2. CodeRover-S on OSS-Fuzz: "Fixing Security Vulnerabilities with AI in OSS-Fuzz", arXiv 2411.03346 (ICSE 2026 SEIP)

**URL:** https://arxiv.org/html/2411.03346v2

**Task**
- Repair of real OSS-Fuzz C/C++ vulnerabilities from ARVO: 588 tasks, each with an exploit input and a sanitizer report.
- Metric: plausible patch.

**Models**
- CodeRover-S and Agentless, both on gpt-4o-2024-08-06.
- VulMaster: 1 plausible patch in total.
- No DeepSeek or MiMo.

**Table 1 — plausible patches by CWE**

| CWE | n | CodeRover-S | Agentless |
|---|---|---|---|
| 121 stack BOF | 244 | 140 (57%) | 77 (32%) |
| 476 NULL deref | 105 | 42 (40%) | 16 (15%) |
| 122 heap BOF | 67 | 46 (69%) | 32 (48%) |
| 416 UAF | 55 | 19 (35%) | 15 (27%) |
| 457 uninit var | 47 | 16 (34%) | 15 (32%) |
| 125 OOB read | 20 | 18 (90%) | 13 (65%) |
| 20 | 12 | 8 (67%) | 6 (50%) |
| 626 | 12 | 6 (50%) | 2 (17%) |
| 120 | 11 | 7 (64%) | 4 (36%) |
| 415 double free | 9 | 4 (44%) | 2 (22%) |
| 590 | 5 | 3 (67%) | 0 (0%) |
| 770 | 1 | 0 | 0 |

**Findings**
- Overall: 52.6% for CodeRover-S (the intro says 52.4%) and 30.9% for Agentless.
- Quote: "adept at patching buffer-overflow and bounds-checking issues", which "usually have well-defined patterns and remediation strategies".
- On UAF and uninitialised variables, the paper cites their "context-dependent nature", needing "a deeper semantic understanding of the program".
- A motivating example (Kamailio) where the fix is in a function that "does not appear in the stack trace".
- No analysis of patch size.

---

### 3. CVE-Factory / LiveCVEBench, arXiv 2602.03012 (2026) — the most recent agentic source

**URL:** https://arxiv.org/html/2602.03012v1

**Task**
- Agents repair reproduced real CVEs from a bug-report-style description.
- 190 tasks across 14 languages (PHP 76, JS 53, Py 48, Shell 44, C 25 …), 74 CWEs.
- The pass criterion for agents is not explicitly defined. Reproductions use test_vuln plus test_func.

**Models**
- **DeepSeek V3.1-Terminus and DeepSeek V3.2**, plus Claude Opus 4.5, Sonnet 4.5, Sonnet 4, GPT-5.1-Codex, Gemini 3 Pro, GLM-4.6, MiniMax M2, Qwen3-Coder-480B.
- Agents: Terminus-2, OpenHands, mini-SWE-agent, Claude Code.

**Table 7 — overall pass %**
- DeepSeek V3.2: 22.75 (Terminus-2), 21.16 (mini-SWE).
- DeepSeek V3.1-Terminus: 23.28 (Terminus-2), 24.34 (mini-SWE), 18.52 (OpenHands).
- Best: Opus 4.5 + Terminus-2 at 42.33. GPT-5.1-Codex: 21.16 (Terminus-2), 12.70 (OpenHands).

**Per CWE** — given only in prose in Appendix C.1, with no per-CWE n for successes and no per-model per-CWE table. Table 9 gives counts only, e.g. CWE-79 n=25, CWE-94 n=12, CWE-22 n=11, CWE-89 n=10.
- "aggregate success ranges from 10.8% on code injection (CWE-94) to 46.6% on OS command injection (CWE-78)".
- Injection-style categories are "generally repaired more often (38–47%)".
- Access control is at 27.1% and path traversal at 17.9%.
- XSS has a mean of 25.1% (sd 6.2).
- "Claude Opus 4.5 achieves 30.6% on code injection versus 4.2% for Claude Sonnet 4.5".

**Language (Appendix C.2)**
- JS 31.4% and PHP 30.7%, versus Py 23.6% and C 23.4%.
- After adjusting for CWE mix, each language falls within ±2.4 points of its expected rate. The authors call language a "second-order effect".
- The same CWE varies sharply by language: CWE-918 85.3% in Py vs 0% in PHP; CWE-78 67.6% in JS vs 5.9% in Py.

---

### 4. PatchAgent, USENIX Security 2025 (Yu et al.)

**URL:** https://cs.uwaterloo.ca/~m285xu/assets/publication/patch_agent-paper.pdf

**Task**
- Agentic repair of 178 real C/C++ vulnerabilities (OSS-Fuzz, Huntr, ExtractFix).
- Success requires passing both the PoC and functional tests.

**Models:** GPT-4o, GPT-4 Turbo, Claude-3 Opus/Sonnet/Haiku. No DeepSeek.

**Table 1**

| Model | Temporal (n=23) | Spatial (n=125) | Null deref (n=23) | Numeric (n=7) | Total |
|---|---|---|---|---|---|
| GPT-4o | 13 (56.52%) | 96 (76.80%) | 23 (100%) | 7 (100%) | 139 (78.09%) |
| GPT-4 Turbo | 11 (47.83%) | 87 (69.60%) | 21 (91.30%) | 7 (100%) | 126 (70.79%) |
| Claude-3 Opus | 14 (60.87%) | 108 (86.40%) | 22 (95.65%) | 7 (100%) | 151 (84.83%) |
| Claude-3 Sonnet | 8 (34.78%) | 77 (61.60%) | 17 (73.91%) | 6 (85.71%) | 108 (60.67%) |
| Claude-3 Haiku | 9 (39.13%) | 93 (74.40%) | 19 (82.61%) | 7 (100%) | 128 (71.91%) |
| Union | 20 (86.96%) | 114 (91.20%) | 23 (100%) | 7 (100%) | 164 (92.13%) |

**Category definitions conflict.** The caption swaps temporal and spatial. The body text defines temporal as UAF, double free and invalid free, and spatial as stack, global and heap overflow.

**Quote:** "most null dereference and numeric errors can often be resolved with a simple if-check, whereas temporal and spatial bugs typically require more complex solutions."

---

### 5. SAN2PATCH, "Logs In, Patches Out", USENIX Security 2025 (Kim et al.)

**URL:** https://www.usenix.org/system/files/usenixsecurity25-kim-youngjoon.pdf

**Task**
- 39 real C vulnerabilities from VulnLoc, plus functionality tests.
- The SAN2VULN set has 27 more.
- Input is the sanitizer log only.

**Models:** GPT-4o (main), GPT-4o-mini, GPT-3.5, Claude 3.5 Sonnet, Gemini 1.5 Pro/Flash. No DeepSeek.

**Table 5 — GPT-4o, by bug type (vulnerability test passed / patch success)**

| Type | Vuln test passed | Patch success |
|---|---|---|
| Integer overflow | 6/6 | 6/6 (100%) |
| Buffer overflow | 22/22 | 18/22 (82%) |
| Divide by zero | 3/4 | 3/4 (75%) |
| Null pointer deref | 2/3 | 2/3 (67%) |
| UAF | 0/2 | 0/2 (0%) |
| Data-type overflow | 2/2 | 2/2 (100%) |

**Table 3 (per-CVE by model).** Totals: GPT-4o 31/39, Claude 3.5 Sonnet 28/39, Gemini 1.5 Pro 18/39, GPT-4o-mini 17/39, Gemini Flash 14/39, GPT-3.5 8/39.
- Both UAF CVEs (libming CVE-2018-8806 and CVE-2018-8964) fail under every model.
- CVE-2018-19664, CVE-2016-8691, CVE-2017-6965 and CVE-2013-7437 also fail under every model.

**Quotes**
- Buffer-overflow success is put down to "the simplicity of patches, such as adding boundary checks near the crash stack trace".
- The four buffer-overflow failures broke functionality because "the patched function was widely used in other parts of the program".

---

### 6. "Why LLMs Fail: A Failure Analysis and Partial Success Measurement…", Al-Maamari, arXiv 2603.10072 (March 2026)

**URL:** https://arxiv.org/html/2603.10072v1

**Task**
- Java, using the Vul4J data but a different study from Wu et al.
- 64 reproducible vulnerabilities across 21 CWEs.
- 5 patches each, zero-shot.

**Model:** Gemini 3.0 Flash only (the intro says 2.0 Flash, which is inconsistent). No DeepSeek.

**Table 5** (n = patches, not vulnerabilities; categories with n≥20 only)

| CWE | n | Compile% | SRS | Fix% |
|---|---|---|---|---|
| 835 | 40 | 100 | 0.725 | 45 |
| 20 | 40 | 95 | 0.469 | 0 |
| 79 | 30 | 83 | 0.489 | 17 |
| 611 | 25 | 80 | 0.516 | 40 |
| 22 | 25 | 72 | 0.458 | 20 |
| 264 | 20 | 100 | 0.573 | 15 |

**Quotes**
- "fix rates ranging from 0% (input validation) to 45% (infinite loop)".
- "Code complexity does not predict difficulty; vulnerability semantics does".
- "Human Patch Size has significant negative Spearman correlation" (ρ=−0.331, p=0.008).
- "143 patches (44.8%) apply an incorrect strategy that also changes program behavior".

---

### 7. VSP chain-of-thought prompting, Nong et al., arXiv 2402.17230

**URL:** https://arxiv.org/html/2402.17230 (Table 15, appendix)

**Task**
- C/C++ single-line-edit repair.
- 170 synthetic SARD samples and 85 real CVE samples.
- Manually judged semantic equivalence.

**Models:** GPT-3.5, Llama2-7B, Falcon-7B (Falcon scored 0 everywhere).

**Table 15 — real CVE subset, GPT-3.5**

| CWE | Standard | Few-shot | VSP |
|---|---|---|---|
| 787 | 13.04% | 13.04% | 17.39% |
| 125 | 6.25% | 31.25% | 25.00% |
| 416 | 0% | 25.00% | 25.00% |
| 476 | 0% | 0% | 0% |
| 190 | 0% | 7.69% | 30.77% |

Micro average with VSP: 20.00%.

**Table 15 — SARD subset, GPT-3.5 VSP:** 787 98.21%, 125 96.43%, 416 100%.

**[inference]** Per-CWE n is not stated. The percentages imply CVE CWE-787 n=46, CWE-125 n=16, CWE-190 n=13.

**Failure causes on CVE:** insufficient context 44.26%, incomplete control-flow 21.31%, oblivion of CWE 19.67%, incomplete data-flow 14.75%. The paper gives no ranking by CWE.

---

### 8. Older, mostly synthetic sources (lower value)

**Wu et al., "Exploring the Limits of ChatGPT in Software Security Applications", arXiv 2312.05275 (2023)**
- URL: https://arxiv.org/pdf/2312.05275
- Synthetic SARD/Juliet cases; success means the vulnerability is no longer exploitable.
- Table 3 (GPT-4 / GPT-3.5):

| CWE | GPT-4 | GPT-3.5 |
|---|---|---|
| 20 | 3/3 | 3/3 |
| 22 | 13/13 | 8/13 |
| 78 | 13/13 | 11/13 |
| 79 | 11/13 | 10/13 |
| 89 | 13/13 | 11/13 |
| 119 | 13/13 | 13/13 |
| 125 | 12/13 | 10/13 |
| 190 | 10/13 | 10/13 |
| 200 | 0/3 | 0/3 |
| 306 | 2/3 | 0/3 |
| 416 | 12/13 | 11/13 |
| 434 | 2/3 | 3/3 |
| 476 | 12/13 | 13/13 |
| 502 | 3/3 | 3/3 |
| 522 | 3/3 | 1/3 |
| 732 | 3/3 | 2/3 |
| 787 | 12/13 | 9/13 |
| 798 | 2/3 | 1/3 |
| Total | 139/154 | 119/154 |

- On 12 real OpenSSL CVEs: "can fix most NULL dereference vulnerabilities … can hardly address other vulnerabilities, especially the ones involving complex application contexts".
- Count inconsistency: Table 4's total row shows 3/12 for both models, but the text says 3 (GPT-3.5) and 4 (GPT-4).

**Pearce et al., IEEE S&P 2023**
- URL: https://arxiv.org/html/2112.02125v3
- Synthetic results, Table II: CWE-787 (C) has 491 functional-and-safe patches out of 22,034 valid, a repair rate of 2.2%. CWE-89 (Python) has 3,197 of 10,796, or 29.6%.
- Hand-crafted scenarios: seven CWEs, all repaired by at least one combination. The per-CWE counts are only in figures.
- Real-world ExtractFix bugs: LLMs fixed 8 of 12.
- Quote: the bugs they failed on "tend to need large code changes (especially additions)".

---

### Adjacent, or no per-CWE repair data (checked)

**SecureAgentBench, arXiv 2509.22097**
- URL: https://arxiv.org/html/2509.22097v1
- This is secure code generation from before the vulnerability was introduced, **not repair**: 105 C/C++ OSS-Fuzz/ARVO tasks.
- Models include **DeepSeek-V3.1**. SWE-agent + DeepSeek-V3.1 is best at 15.2% correct-and-secure.
- Per CWE it only has Figure 6, the share of correct code that is still vulnerable: "in CWE-120 more than 80% of the correct code remains vulnerable, whereas in CWE-415 the proportion is only about 10%".

**PatchEval, arXiv 2511.11019**
- URL: https://arxiv.org/html/2511.11019v1
- **No per-CWE data.**
- Includes **DeepSeek-R1 (0528) and V3 (0324)**. With a location oracle, out of 230: R1 44, V3 41, best LLM Gemini-2.5-Pro 52, SWE-Agent-Gemini 53 (Table 3).
- Factor table (Table 9), average repaired / group size:

| Factor | Bucket | Repaired / group |
|---|---|---|
| Lines | 1–5 | 19.2/59 |
| Lines | 20–50 | 4.6/46 |
| Lines | 50+ | 0.4/19 |
| Hunks | 1 | 30.4/120 |
| Hunks | 2 | 10.6/69 |
| Hunks | 3+ | ≈0 |
| Files | 1 | 41.5/202 |
| Files | 2 | 1.3/21 |
| Files | 3+ | 0 |

- Quote: "it drops to 7.7% for complex CVEs (patches modifying 20+ lines)".

**Other studies with no per-CWE results**
- ZeroDayBench, arXiv 2603.02297: 22 tasks porting real CVEs into similar repos. Results are by information level, not CWE. Zero-day pass rates: Claude Sonnet 4.5 12.8%, GPT-5.2 14.4%, Grok 4.1 12.1%. With a CWE hint: 32.9%, 32.9% and 18.0%.
- Big-Vul metrics study, arXiv 2609.26749: uses DeepSeek-Coder 1.3B/6.7B.
- NAVRepair, arXiv 2405.04994: DeepSeek-Coder-6.7B; results are by AST edit-node type, not CWE.
- EvoRepair, arXiv 2605.30105: DeepSeek-v3.1 on PatchEval improved from 136 to 163 fixes.
- VulnResolver, arXiv 2601.13933: DeepSeek-V3.2-Exp on SEC-bench. SEC-bench Full averages 2.43 hunks and 17.29 lines per issue, versus 1.59 and 11.03 for Lite, and the paper links Full's lower resolve rate to this.
- MemRepair, arXiv 2605.17444: DeepSeek-v3.2. By language, Python is hardest (46.2%) and JS easiest (74.7%).
- VRpilot, arXiv 2405.15690.
- VulnLLMEval, arXiv 2409.10756: metrics are similarity-based.
- Defects4C vul subset, arXiv 2510.11059: failure patterns include multi-hunk patches and deletion-centric fixes, but no per-CWE results seen.
- APPATCH (USENIX Security 2025) and Google's "AI-powered patching" (15% overall; full text not accessible) were not checked in full.

---

### Patterns across sources [inference — the papers do not state these as joint conclusions]

- **Hard in at least two of these studies:**
  - CWE-416 use-after-free: source 2 (35%), source 4 (temporal is the lowest category), source 5 (0/2, fails on every model).
  - CWE-125 out-of-bounds read, when real code is graded by exact match: 0% for GPT-4o in source 1. But it reaches 90% plausible in source 2 when an exploit and sanitizer log are given. Which way it goes depends on the grading and inputs.
  - CWE-835 infinite loop: low in source 1, but 45% in source 6.
  - CWE-20 input validation: 0% in source 6.
  - CWE-94 code injection: 10.8% in source 3.
  - CWE-22 path traversal: 17.9% in source 3, about 20% in sources 1 and 6.
- **Easy:**
  - Null dereference and numeric bugs when a crash log exists (sources 4 and 5).
  - Authentication CWEs such as 287 and 306 under exact match (source 1).
  - OS and command injection (sources 1 and 3).
- **Largest stated factor:** patch size, hunks and files (PatchEval, source 6, Pearce).
- **Language:** called "second-order" in source 3, whereas source 1 finds C/C++ worst and Go best.
