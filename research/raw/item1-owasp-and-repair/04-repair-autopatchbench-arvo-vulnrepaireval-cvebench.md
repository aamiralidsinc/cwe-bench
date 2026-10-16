<!-- Verbatim final report of a research sub-agent (id a83999a35e7ce1464), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

# How well LLMs and agents repair vulnerabilities, broken down by CWE or crash class (as of 2026-10-16)

The richest per-class source is Collinear's CWE-bench. Its OWASP heatmap (the "Figure 5" image) and a full per-CWE table are published as JavaScript data files on cwe-bench.com. I downloaded and parsed them, so the numbers below come from the data, not from reading an image.

The only other real per-CWE repair table is in the CodeRover-S paper (ARVO, GPT-4o).

On the models you asked about:
- **Xiaomi MiMo:** appears in none of the sources.
- **DeepSeek:** appears in CWE-bench v0 and v1, VulnRepairEval, and WilliamT.

---

## 1. Meta CyberSecEval 4 / AutoPatchBench

- **Task type:** repair of real fuzzing crashes. The bugs are ARVO OSS-Fuzz bugs; the language is C/C++.
- **Size:**
  - The blog says 136 samples (Lite: 113, "root cause of the crash is confined to a single function").
  - The repo README says 142 (`autopatch_bench.json`), 120 (`autopatch_lite.json`, "fixable with one hunk") and 20 (`autopatch_samples.json`).
  - The blog says the set has "11 distinct crash types" but never names them.
- **Models:**
  - Only two are named. Gemini 1.5 Pro: "61.1% patch generation success rate", with 5.3% of the total judged correct. Llama 4 Maverick: 73 patches.
  - Figure 2 (unnamed models): about 60% generation success and about 5–11% after verification.
  - Table 1 (Maverick, n=44): human pass 5; differential-test pass 12; precision 41.7%; recall 100%.
  - No DeepSeek, no MiMo.
- **Per crash type: no per-CWE data.**
  - There is no per-crash-type data in the blog, the InfoQ article, the README or the CyberSecEval site.
  - The dataset files contain only ARVO IDs and no results, so a breakdown cannot be computed.
- **Difficulty statements (blog):**
  - "Frequently, crashes are the result of state contamination that occurs prior to the crash being triggered."
  - "none of the functions within the stack frames may include the code responsible for the root cause."
  - "when root causes are distributed across multiple locations within the code … the difficulty of generating a correct patch increases significantly."
  - "We observed that cheating happens more frequently when we request the LLM to retry within the same trajectory."
- **URLs:**
  - https://engineering.fb.com/2025/04/29/ai-research/autopatchbench-benchmark-ai-powered-security-fixes/
  - https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks
  - https://www.infoq.com/news/2025/05/meta-autopatchbench-ai-patching
  - I found no arXiv paper for AutoPatchBench.

## 2. Other repair evaluations built on ARVO or OSS-Fuzz

### 2a. CodeRover-S, "Fixing Security Vulnerabilities with AI in OSS-Fuzz" (arXiv 2411.03346v2)

- **Setup:** repair of 588 real ARVO bugs in C/C++. Both CodeRover-S and the Agentless baseline use gpt-4o-2024-08-06. No DeepSeek or MiMo.
- **Overall:** 52.4% plausible patches in the abstract, but 52.6% in §4.1 (the paper contradicts itself).
- **Table 1, "Analysis of plausible patches according to CWE Type"** (exact numbers; "plausible" means the exploit no longer crashes):

| CWE | n | CodeRover-S | Agentless |
|---|---|---|---|
| CWE-121 Stack-based Buffer Overflow | 244 | 140 (57%) | 77 (32%) |
| CWE-476 NULL Pointer Dereference | 105 | 42 (40%) | 16 (15%) |
| CWE-122 Heap-based Buffer Overflow | 67 | 46 (69%) | 32 (48%) |
| CWE-416 Use After Free | 55 | 19 (35%) | 15 (27%) |
| CWE-457 Use of Uninitialized Variable | 47 | 16 (34%) | 15 (32%) |
| CWE-125 Out-of-bounds Read | 20 | 18 (90%) | 13 (65%) |
| CWE-20 Improper Input Validation | 12 | 8 (67%) | 6 (50%) |
| CWE-626 Null Byte Interaction Error | 12 | 6 (50%) | 2 (17%) |
| CWE-120 Buffer Copy w/o Checking Size | 11 | 7 (64%) | 4 (36%) |
| CWE-415 Double Free | 9 | 4 (44%) | 2 (22%) |
| CWE-590 Free of Memory not on the Heap | 5 | 3 (67%) | 0 (0%) |
| CWE-770 Allocation w/o Limits | 1 | 0 (0%) | 0 (0%) |

- **Hardest and easiest classes (quotes):**
  - "CodeRover-S performs better on buffer-related vulnerabilities, specifically CWE-121, CWE-122, and CWE-125."
  - "CodeRover-S struggles with other memory management-related vulnerabilities such as CWE-416 and CWE-457", which it attributes to "the context-dependent nature of these vulnerabilities."
- **Root cause vs crash site:** discussed only qualitatively, through the Kamailio-38065 example, where the fix "modifies the `skip_name` function, which does not appear in the stack trace."
- **URL:** https://arxiv.org/html/2411.03346v2

### 2b. PatchBench (Li, Mahajan, Tian, Kwon, Chen; arXiv 2609.04075)

- **Setup:** ARVO bugs that were transplanted and mutated to reduce memorisation. 213 tasks, 32 projects, "16 distinct CWE types", C/C++.
- **Selection:** tasks were chosen so the fix lies outside the crash stack (trace overlap ρ ≤ 1/2).
- **Agents:** 11, using GPT-5.6 Sol, Opus 4.8, GPT-5, Sonnet 4.5, Gemini 3.5 Flash, Gemini 3.1 Pro, plus the AIxCC systems Atlantis, Buttercup and RoboDuck. No DeepSeek or MiMo.
- **Table 2, solved / PoC-only pass (%):**
  - Codex + GPT-5.6 Sol: 59.2 / 97.2
  - OpenHands + GPT-5.6 Sol: 58.2 / 98.1
  - Claude Code + Opus 4.8: 56.8 / 97.7
  - Atlantis: 48.4 / 92.0
  - OpenHands + Opus 4.8: 47.9 / 93.0
  - OpenHands + Gemini 3.5 Flash: 44.1 / 77.9
  - Buttercup: 42.7 / 72.3
  - OpenHands + GPT-5: 42.3 / 96.2
  - OpenHands + Sonnet 4.5: 38.0 / 85.9
  - OpenHands + Gemini 3.1 Pro: 31.5 / 57.7
  - RoboDuck: 29.6 / 46.5
- **Per CWE: no per-CWE data** in the text I read, including the appendix Tables 3–4.
- **Factors:**
  - "81% of Codex + GPT-5.6 Sol's patches modify functions on the crash stack trace."
  - For tasks whose developer fix lies outside the stack, "64% of such agent patches are still found in functions on the trace."
  - PoC-only checking overstates solve rates 1.83× (83.1% of patches remove the PoC crash, but 45.3% of tasks are solved).
  - "67 out of 213 patching tasks cannot be solved by any of the 11 agents."
- **URL:** https://arxiv.org/html/2609.04075v1

### 2c. WilliamT, "Fixing 7,400 Bugs for 1$" (arXiv 2505.13103)

- **Setup:** 358 ARVO bugs of four crash types (heap overflow, stack overflow, use-after-free, global overflow).
- **DeepSeek:** used as backends. DeepSeek reasoner made 159 fixes and DeepSeek chat 158.
- **Other results:** CodeRover-S 54.5%, WilliamT (GPT-4o) 46.1%, Agentless 33.8%, WilliamT + CodeRover-S 73.5%.
- **Per crash type: no per-crash-type data.** Only the ARVO mix is given: HBO 52.3%, UAF 11.3%, SBO 8.9%, GBO 4.6%.
- **Quote:** "generating a patch just before the crash point is sufficient to mitigate exploitation."
- **URL:** https://arxiv.org/html/2505.13103

### 2d. CyberGym-E2E (arXiv 2606.04460, ICML 2026)

- **Setup:** OSS-Fuzz bugs, partly drawn from ARVO and CyberGym; C/C++. Tasks cover discovery, PoC generation and patching. 615 and 920 tasks.
- **Models:** Opus 4.5/4.6, Sonnet 4.5, GPT-5.2-Codex, GPT-5.4, Gemini 3/3.1 Pro. No DeepSeek or MiMo.
- **Patch-only success:**
  - Table 3 (615 tasks): Opus 4.5 82.3, Sonnet 4.5 (Claude Code) 77.4, Gemini 3 Pro 77.6, GPT-5.2-Codex 58.5.
  - Table 4 (920 tasks): GPT-5.4 87.1, Opus 4.6 84.1, Gemini 3.1 Pro 83.0.
- **Per crash type: no per-crash-type or per-CWE data.**
- **Quotes:**
  - "vulnerability discovery, rather than patch generation, is the primary bottleneck."
  - "many successful agent patches address the same root cause as the ground-truth patch but at a different location."
- **URL:** https://arxiv.org/html/2606.04460

### 2e. Related, but not ARVO

- **SEC-bench** (arXiv 2506.11791): OSV/OSS-Fuzz C/C++ bugs, 200 verified instances. Best patch rate is 34.0%. No per-type patching numbers. Gold patches average 17.3 lines, 1.3 files and 1.6 functions. https://arxiv.org/html/2506.11791v2
- **Original CyberGym:** PoC reproduction only. Its per-crash-type numbers (for example heap-buffer-overflow READ 17.9%) are PoC numbers, not repair.

## 3. VulnRepairEval (Wang et al., arXiv 2509.03331)

- **Setup:** repair of 23 real Python CVEs. A repair counts only if the working PoC exploit fails afterwards. The paper says "nine different vulnerability types", but names and counts appear only in the Figure 1 image.
- **Models (Table 3, P_succ):**
  - Gemini 2.5 Pro 0.217
  - **DeepSeek R1 671B 0.174**
  - **DeepSeek V3 671B 0.130**
  - Gemini 2.5 Flash, Gemini 2.0 Flash and Qwen3 235B Thinking: 0.087 each
  - o4-mini and GPT-3.5 Turbo: 0.043 each
  - GPT-4o, Qwen3 8B, Qwen3 8B Thinking and Qwen3 235B: 0
  - No MiMo.
- **Published per-CWE data: no per-CWE data.**
  - The paper publishes a per-CVE grid in Table 6, which I re-parsed from the HTML and verified.
  - It also gives difficulty tiers in Table 4 (Easy / Medium / Hard fixed counts): Gemini 2.5 Pro 3/2/0; DeepSeek R1 2/1/1; the others 0–2.
- **My own grouping of Table 6 by its "Description" column** (fixed count per model; columns are Gemini 2.5 Pro, Gemini 2.5 Flash, o4-mini, DeepSeek R1, Qwen3 8B Thinking, Qwen3 235B Thinking):

| Class (my grouping) | n | G-Pro | G-Flash | o4-mini | DS-R1 | Q8B-T | Q235B-T |
|---|---|---|---|---|---|---|---|
| Unsafe YAML deserialisation → RCE | 3 | 3 | 1 | 0 | 2 | 0 | 2 |
| Command, argument or code injection (incl. dynamic eval) | 5 | 2 | 1 | 1 | 1 | 0 | 0 |
| ReDoS | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| XSS | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Path traversal / file access | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Other DoS (decompression bomb, recursion) | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Crash (integer overflow, NULL dereference) | 2 | 0 | 0 | 0 | 1 | 0 | 0 |
| Protocol (request smuggling, header injection) | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Crypto logic leading to auth bypass | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

- **Stated findings:**
  - "LLMs are generally proficient at repairing straightforward flaws". Easy flaws are "localized to a single high-risk function".
  - LLMs "consistently struggle with vulnerabilities that demand deep contextual understanding". Hard flaws are "algorithmic or design-level flaws" that "may involve large-scale refactoring across multiple components".
  - "the predominant failure is the inability of LLMs to localize the vulnerability". Localisation causes "roughly 60–78%" of failures, and patch errors about 20%.
  - Generated patches were mostly confined to a single file.
- **URL:** https://arxiv.org/html/2509.03331

## 4. CVE-Bench (three different benchmarks share this name)

### 4a. Zhu, Kang et al. (arXiv 2503.17332): exploitation, not repair

- **Setup:** 40 critical web-application CVEs. Agents are Cy-Agent, T-Agent and AutoGPT on gpt-4o. No DeepSeek or MiMo.
- **Results:** "up to 13%" exploited (§4.2 says 10% zero-day and 12.5% one-day).
- **Per class:** Table 6 lists the attack types, but success per type is given only in figures. The main stated bottleneck is "insufficient exploration".
- **URL:** https://arxiv.org/html/2503.17332

### 4b. Wang, Liu, Xiao (NAACL 2025): repair

- **Setup:** 509 real CVEs from CVEfixes in Python, Java, JavaScript and PHP, from 120 repositories. "Over 16 types of CWEs" (Table 2 gives counts only). SWE-agent with GPT-4, GPT-3.5 and Llama-3. No DeepSeek or MiMo.
- **Per CWE: no per-CWE data.**
- **Per language (Table 1, GPT-4, white-box):**

| Language | Repaired # | Repaired % | Edit lines |
|---|---|---|---|
| Python | 15 | 21.17 | 74.00 |
| Java | 53 | 12.33 | 34.90 |
| JavaScript | 127 | 17.81 | 43.23 |
| PHP | 38 | 16.33 | 34.34 |

- **Other results:** black-box 14.1%, intermediate 17.8%, white-box "over 21%". Under black-box the main failure is localisation.
- **Quote on Java:** "may be due to the GPT-4's training dataset … Furthermore, the syntax complexity of Java is also higher".
- **URL:** https://aclanthology.org/2025.naacl-long.212.pdf

### 4c. Gatti Pinheiro (2026): repair

- **Setup:** 20 Python CVEs across 15 CWE categories. Agents are gpt-5.5, gpt-5.4-mini, gpt-5.4-nano, laguna-m.1 and laguna-xs.2.
- **Results:** best is 50% (gpt-5.5, 30/60).
- **Per CWE:** a per-CWE heatmap exists, but the SVG carries only colours, no numbers. Per-run JSON results in the repo could be used to compute one; I did not do this.
- **Quotes:**
  - "Four CVEs were not solved by any model across all 15 runs".
  - The curation "skews the set toward vulnerabilities with compact, self-contained patches".
- **URLs:** https://giovannigatti.github.io/cve-bench/ and https://github.com/giovannigatti/cve-bench

## 5. Collinear CWE-bench

- **Task type:** "audit-and-patch" of real repositories. Some tasks reproduce disclosed CVEs, and "every task carries additional vulnerabilities of the same class that the published fix does not reach".
  - The agent receives no CVE identifier, file or line.
  - A task passes only when a deterministic PoC check is blocked and all pre-existing tests still pass.
  - v1 adds a three-judge panel.
- **v0 (blog, Sep 2):** 100 tasks, 54 CWEs. Languages: C/C++ 34, Go 21, JS/TS 20, Java 18, Python 4, Rust 3.
- **v1 (Sep 25):** 120 tasks, 73 CWEs, one CWE per task. Languages: C/C++ 31, Go 26, JS/TS 26, Java 20, Python 14, Rust 3. Four rollouts per task.
- **DeepSeek, overall:**
  - v0, DeepSeek-V4-Flash: 30.4% at $0.13 per rollout.
  - v1, DeepSeek-V4.1-Flash: programmatic pass@1 55%, pass@4 74%; judge pass@1 53%, pass@4 75%; $0.09 per rollout. Tied 7th.
  - No MiMo in either version.
- **Data source:** the OWASP heatmap and per-CWE numbers come from page data files:
  - https://cwe-bench.com/assets/charts/data-v1.js
  - https://cwe-bench.com/assets/charts/cwe-map-data-v1.js
  - https://cwe-bench.com/assets/charts/data.js (v0)
  - https://cwe-bench.com/assets/charts/cwe-map-data.js (v0)
  - The v1 OWASP values match the HTML table shown on https://cwe-bench.com.

### 5a. v1, deterministic pass@1 by OWASP category (data-v1.js `owasp.values`)

The n column is my own sum of per-CWE task counts from cwe-map-data-v1.js. The last two columns are my own computations.

| OWASP | n | Grok 4.7 | Gemini 4 Argon | GPT-6 Astra | Opus 5.5 | Fable 5.1 | Grok 4.6 | **DeepSeek V4.1 Flash** | Muse Spark 1.3 | Hy4 Prev | GPT-6 Sol | Inkling | Mean of 11 (mine) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A01 Broken Access Control | 13 | 83 | 92 | 75 | 83 | 69 | 83 | **65** | 65 | 65 | 71 | 40 | 71.9 |
| A02 Security Misconfiguration | 11 | 75 | 66 | 75 | 75 | 64 | 57 | **57** | 55 | 61 | 43 | 55 | 62.1 |
| A03 Supply Chain Failures | 10 | 63 | 75 | 58 | 65 | 65 | 58 | **60** | 60 | 50 | 58 | 43 | 59.5 |
| A04 Cryptographic Failures | 13 | 87 | 83 | 85 | 90 | 81 | 75 | **65** | 69 | 63 | 71 | 54 | 74.8 |
| A05 Injection | 14 | 70 | 55 | 89 | 63 | 66 | 48 | **54** | 45 | 54 | 54 | 32 | 57.3 |
| A06 Insecure Design | 12 | 50 | 67 | 52 | 52 | 50 | 54 | **42** | 44 | 48 | 35 | 31 | 47.7 |
| A07 Authentication Failures | 13 | 52 | 58 | 63 | 60 | 42 | 52 | **58** | 62 | 48 | 42 | 33 | 51.8 |
| A08 Software/Data Integrity Failures | 11 | 57 | 36 | 41 | 39 | 27 | 36 | **39** | 36 | 23 | 39 | 27 | **36.4** |
| A09 Logging & Alerting Failures | 10 | 75 | 70 | 65 | 65 | 53 | 50 | **55** | 63 | 58 | 53 | 33 | 58.2 |
| A10 Exceptional Conditions | 13 | 63 | 71 | 67 | 77 | 62 | 54 | **52** | 52 | 58 | 54 | 21 | 57.4 |

**v1 by language (data-v1.js):**
- DeepSeek V4.1 Flash: C/C++ 60, Go 61, Java 46, JS/TS 56, Python 46, Rust 42.
- Mean of 11 models (mine): C/C++ 60.6, Go 59.1, Java 52.0, JS/TS 61.0, Python 54.2, Rust 52.5.
- Site heading: "JS/TS and C/C++ lead, Java and Rust trail".

### 5b. v0, pass@1 by OWASP category (data.js)

| OWASP | n | DeepSeek V4 Flash | Mean of 14 (mine) |
|---|---|---|---|
| A01 | 10 | 12 | 34.1 |
| A02 | 9 | 47 | 49.5 |
| A03 | 10 | 38 | 43.8 |
| A04 | 11 | 33 | 39.8 |
| A05 | 11 | 38 | 35.7 |
| A06 | 8 | 19 | 24.8 |
| A07 | 11 | 14 | **13.6** |
| A08 | 9 | 19 | 17.8 |
| A09 | 10 | 29 | 34.1 |
| A10 | 11 | 23 | 21.9 |

**v0 by language, DeepSeek V4 Flash:** C/C++ 25, Go 15, Java 20, JS/TS 53, Python 19, Rust 0.

### 5c. v1, per-CWE pass@1 (cwe-map-data-v1.js)

- Values are the percentage of rollouts passing over n tasks × 4 rollouts.
- Rows are sorted by my mean over 11 models.
- Most rows have n = 1–2, so treat each row as anecdotal.

| CWE | OWASP | n | DS V4.1 Flash | Opus 5.5 | GPT-6 Astra | Grok 4.7 | Gemini 4 Argon | Mean of 11 (mine) |
|---|---|---|---|---|---|---|---|---|
| CWE-307 excessive auth attempts | A07 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| CWE-345 data authenticity | A08 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| CWE-444 HTTP request smuggling | A06 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| CWE-1357 untrustworthy component | A03 | 2 | 0 | 0 | 25 | 0 | 0 | 2 |
| CWE-362 race condition | A06 | 1 | 0 | 0 | 0 | 25 | 0 | 2 |
| CWE-252 unchecked return value | A10 | 1 | 0 | 0 | 100 | 0 | 0 | 9 |
| CWE-913 dynamically-managed code | A06 | 1 | 0 | 0 | 50 | 0 | 50 | 9 |
| CWE-502 deserialization | A08 | 2 | 0 | 0 | 0 | 50 | 25 | 9 |
| CWE-601 open redirect | A01 | 1 | 0 | 0 | 0 | 25 | 75 | 14 |
| CWE-613 session expiration | A07 | 2 | 25 | 25 | 50 | 0 | 50 | 21 |
| CWE-310 crypto issues | A02 | 1 | 0 | 0 | 100 | 0 | 100 | 23 |
| CWE-494 download w/o integrity | A08 | 1 | 25 | 50 | 50 | 50 | 50 | 23 |
| CWE-1336 SSTI | A05 | 2 | 0 | 0 | 50 | 50 | 13 | 24 |
| CWE-269 privilege mgmt | A06 | 1 | 50 | 0 | 0 | 75 | 50 | 25 |
| CWE-829 untrusted control sphere | A08 | 2 | 50 | 25 | 0 | 50 | 50 | 27 |
| CWE-79 XSS | A05 | 2 | 25 | 63 | 75 | 0 | 38 | 30 |
| CWE-288 auth bypass alt path | A07 | 1 | 75 | 50 | 25 | 25 | 75 | 39 |
| CWE-306 missing auth | A07 | 2 | 50 | 50 | 50 | 25 | 50 | 41 |
| CWE-476 NULL deref | A10 | 2 | 50 | 88 | 0 | 63 | 50 | 42 |
| CWE-532 sensitive info in log | A09 | 5 | 35 | 40 | 50 | 70 | 60 | 43 |
| CWE-942 permissive CORS | A02 | 2 | 25 | 63 | 50 | 88 | 13 | 45 |
| CWE-1395 vulnerable dependency | A03 | 3 | 33 | 67 | 33 | 67 | 83 | 47 |
| CWE-93 CRLF injection | A05 | 3 | 25 | 42 | 100 | 92 | 50 | 48 |
| CWE-703 exceptional conditions | A10 | 2 | 50 | 50 | 50 | 50 | 100 | 48 |
| CWE-354 integrity check value | A08 | 1 | 75 | 0 | 0 | 100 | 0 | 48 |
| CWE-674 uncontrolled recursion | A10 | 1 | 0 | 100 | 100 | 50 | 0 | 50 |
| CWE-16 configuration | A02 | 1 | 50 | 100 | 100 | 100 | 0 | 52 |
| CWE-693 protection mech failure | A06 | 2 | 13 | 100 | 50 | 50 | 50 | 54 |
| CWE-347 crypto signature verification | A04 | 2 | 25 | 100 | 100 | 50 | 50 | 55 |
| CWE-755 exceptional conditions | A10 | 2 | 38 | 100 | 63 | 50 | 88 | 56 |
| CWE-327 broken crypto algorithm | A04 | 3 | 33 | 67 | 33 | 83 | 92 | 56 |
| CWE-73 external file name control | A06 | 1 | 75 | 25 | 0 | 100 | 100 | 57 |
| CWE-290 spoofing auth bypass | A07 | 1 | 50 | 25 | 100 | 100 | 75 | 57 |
| CWE-639 user-controlled key | A01 | 2 | 63 | 63 | 100 | 63 | 100 | 58 |
| CWE-770 unbounded allocation | A06 | 1 | 100 | 25 | 100 | 25 | 100 | 59 |
| CWE-915 object attribute modification | A08 | 2 | 50 | 63 | 100 | 100 | 50 | 60 |
| CWE-497 system info exposure | A01 | 1 | 25 | 100 | 100 | 50 | 50 | 61 |
| CWE-1321 prototype pollution | A08 | 1 | 50 | 100 | 100 | 75 | 0 | 61 |
| CWE-441 unintended proxy | A01 | 1 | 25 | 100 | 0 | 100 | 100 | 64 |
| CWE-1004 cookie w/o HttpOnly | A02 | 1 | 100 | 100 | 75 | 25 | 100 | 66 |
| CWE-295 certificate validation | A07 | 2 | 63 | 100 | 50 | 100 | 50 | 67 |
| CWE-94 code injection | A05 | 2 | 75 | 88 | 100 | 75 | 100 | 67 |
| CWE-326 weak encryption strength | A04 | 1 | 50 | 100 | 100 | 100 | 100 | 68 |
| CWE-522 credential protection | A06 | 2 | 50 | 88 | 100 | 50 | 100 | 69 |
| CWE-614 cookie w/o Secure | A02 | 2 | 63 | 63 | 100 | 63 | 100 | 69 |
| CWE-338 weak PRNG | A04 | 1 | 50 | 100 | 100 | 75 | 25 | 70 |
| CWE-117 log neutralization | A09 | 5 | 75 | 90 | 80 | 80 | 80 | 73 |
| CWE-116 output encoding | A05 | 1 | 75 | 75 | 100 | 100 | 25 | 73 |
| CWE-611 XXE | A02 | 2 | 75 | 88 | 63 | 100 | 50 | 73 |
| CWE-863 incorrect authorization | A01 | 2 | 63 | 100 | 88 | 100 | 100 | 73 |
| CWE-297 host mismatch | A07 | 3 | 83 | 83 | 100 | 67 | 67 | 73 |
| CWE-369 divide by zero | A10 | 3 | 67 | 75 | 83 | 83 | 92 | 73 |
| CWE-862 missing authorization | A01 | 2 | 75 | 100 | 50 | 100 | 88 | 74 |
| CWE-20 input validation | A05 | 1 | 100 | 100 | 100 | 100 | 0 | 75 |
| CWE-565 cookies w/o validation | A08 | 1 | 75 | 100 | 100 | 0 | 100 | 75 |
| CWE-1284 quantity validation | A06 | 1 | 50 | 100 | 100 | 75 | 100 | 77 |
| CWE-489 active debug code | A02 | 1 | 100 | 100 | 25 | 100 | 100 | 80 |
| CWE-1329 non-updatable component | A03 | 2 | 100 | 75 | 88 | 63 | 100 | 80 |
| CWE-208 timing discrepancy | A04 | 1 | 100 | 75 | 100 | 100 | 100 | 84 |
| CWE-209 error message info leak | A10 | 1 | 100 | 100 | 100 | 100 | 100 | 86 |
| CWE-89 SQLi | A05 | 2 | 100 | 88 | 100 | 75 | 100 | 86 |
| CWE-390 error w/o action | A10 | 1 | 100 | 100 | 100 | 100 | 75 | 89 |
| CWE-776 XML entity expansion | A02 | 1 | 50 | 100 | 100 | 100 | 100 | 89 |
| CWE-319 cleartext transmission | A04 | 1 | 100 | 100 | 100 | 100 | 100 | 91 |
| CWE-330 insufficient randomness | A04 | 2 | 100 | 100 | 100 | 100 | 100 | 93 |
| CWE-470 unsafe reflection | A05 | 1 | 100 | 100 | 100 | 100 | 100 | 95 |
| CWE-918 SSRF | A01 | 2 | 100 | 88 | 100 | 88 | 100 | 96 |
| CWE-1104 unmaintained component | A03 | 3 | 100 | 100 | 83 | 100 | 100 | 96 |
| CWE-22 path traversal | A01 | 1 | 100 | 75 | 100 | 100 | 100 | 98 |
| CWE-434 unrestricted upload | A06 | 1 | 100 | 100 | 75 | 100 | 100 | 98 |
| CWE-916 weak password hash | A04 | 2 | 100 | 100 | 100 | 100 | 88 | 98 |
| CWE-285 improper authorization | A01 | 1 | 100 | 100 | 100 | 100 | 100 | 100 |
| CWE-287 improper authentication | A07 | 1 | 100 | 100 | 100 | 100 | 100 | 100 |

### 5d. v0, per-CWE (cwe-map-data.js), DeepSeek V4 Flash / mean of 14 models (mine)

- **Zero for every model:** CWE-494, 252, 345, 444 (n=1 each). CWE-1357 (n=2) is 0 for DeepSeek, with a mean of 0.
- **Near zero:**
  - CWE-502: DeepSeek 12, mean 3
  - CWE-613: 0, mean 4
  - CWE-290: 0, mean 4
  - CWE-829: 0, mean 4
  - CWE-295: 0, mean 6
  - CWE-79: 0, mean 8
  - CWE-362: 0, mean 9
  - CWE-863: 0, mean 11
- **Highest means:**
  - CWE-1104: DeepSeek 92, mean 96
  - CWE-434: 100, mean 89
  - CWE-89: 100, mean 86
  - CWE-20: 100, mean 83
  - CWE-776: 33, mean 81
  - CWE-22: 50, mean 80
- **Caveat:** some v0 values for single-task CWEs are not multiples of 25 (for example DeepSeek CWE-116 = 67). The file header says "leaves whose agent produced no work are excluded", so some denominators are smaller.

### 5e. Stated findings

- **Site headings:**
  - v1: "models share weaknesses in data integrity (A08), insecure design (A06), and authentication (A07)".
  - v0: "models share weaknesses across categories such as authentication (A07), error handling (A10), and data integrity (A08)".
- **v1 blog:**
  - "The unsolved nine span six languages, and three of them are Software or Data Integrity Failures (OWASP A08)."
  - "One of the ten is solved only by DeepSeek V4.1 Flash and Hy4 Preview."
  - "All three solve 75 tasks in common, and together they solve 110."
- **v0 blog:** agents "fail later, when the fix isn't where the bug is or doesn't have an obvious shape." It names four failure patterns:
  - Incomplete fixes: "closing two of the three still scores zero."
  - Trusting a defence that does not work: "so the check proves nothing."
  - Over-correction: "The fix works, but it breaks the product."
  - Reasoning that stops one step early: "The fix should've occurred where tokens are created, not where they are canceled."
- **Site failure taxonomy:** localisation, missed detection, wrong invariant, incomplete remediation.
- **No stated link to fix size or files touched.**
- **v0 → v1 rescoring of the same 100 tasks:** "the verifiers moved more than the models". For example, Hy4 Preview went from 33.8% to 55.8%.

### 5f. Inconsistencies in the CWE-bench material

- The hidden v0 block of the HTML contains a stale OWASP table that uses v1 model names, has no Gemini column, and has slightly different numbers. I used the JS data files instead.
- The v0 FAQ says 10 of 100 tasks are unsolved by every model, while the v0 tile says 18 of 100.
- The v0 blog says each OWASP category has ten tasks, while the data shows 8–11.

**URLs:**
- https://blog.collinear.ai/p/cwe-bench
- https://blog.collinear.ai/p/cwe-bench-v1
- https://cwe-bench.com

---

## Cross-source pattern

Stated by the sources:
- Localisation, or a fix that belongs away from the crash or symptom site, is the main driver of failure. This is said by AutoPatchBench, PatchBench, VulnRepairEval, CVE-Bench (NAACL), CWE-bench and CyberGym-E2E.
- Multi-site and design-level fixes are harder. This is said by VulnRepairEval, the AutoPatchBench blog, CWE-bench, and Java/Vul4J study arXiv 2511.23408 ("None of the LLMs produced both edits in the same patch").

My inference:
- The classes that repeatedly score low are integrity/authenticity, deserialisation, session and authentication logic, races, request smuggling, and use-after-free or uninitialised memory.
- The classes that repeatedly score high are single-sink injection (SQLi, path traversal, SSRF), weak crypto parameters, and bounds-check buffer overflows.
