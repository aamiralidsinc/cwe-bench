<!-- Verbatim final report of a research sub-agent (id a68621d65a777db4e), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

## Per-CWE evidence on secure code GENERATION benchmarks (research as of 2026-10-16)

I used arXiv HTML pages and project leaderboards. I parsed tables locally from downloaded HTML, so the numbers below are copied exactly. Nothing was written to the repo.

**Overall result:**
- Real per-CWE × per-model numbers in text form exist **only for BaxBench**: Appendix D.2, Tables 12–14, with DeepSeek-R1 and DeepSeek-V3.
- SecRepoBench and SecCodePLT have per-CWE results **only as figure images**.
- CWEval and CyberSecEval publish **no per-CWE data**.
- **No Xiaomi MiMo results** appear in any of these benchmarks, papers or leaderboards.

---

### 1. BaxBench (ETH SRI). GENERATION of whole backend apps
- **Task:** generate a complete backend from an OpenAPI spec or a text spec. Graded by functional tests plus expert-written end-to-end exploits.
- **Size:** 28 scenarios × 14 frameworks = 392 tasks, in 6 languages (Go, JS, PHP, Python, Ruby, Rust). 13 CWEs, about 3.3 per scenario.
- **Paper:** arXiv 2502.11844v3 (30 May 2025, ICML 2025). https://arxiv.org/html/2502.11844
- **Paper models (11):** o1, o3-mini, GPT-4o, Claude-3.5 Sonnet, **DeepSeek-R1, DeepSeek-V3**, Codestral, Qwen2.5 Coder, Llama-3.3 70B, Qwen2.5 72B, Qwen2.5 7B.
- **Leaderboard (https://baxbench.com):** 38 models.
  - The data files are `/static/data/leaderboard_data_{none,generic,specific}.json`. Their HTTP Last-Modified header is 22 May 2026; the page itself shows no update date.
  - DeepSeek entries: R1, V3, "V3 03-24", and R1-Distill models. No V3.1, V3.2 or V4, and no MiMo.
  - With no security prompt, sec_pass@1 / pass@1 are:
    - Claude Opus 4.5 Thinking: 56.1 / 86.2 (best)
    - GPT-5: 54.3 / 70.7
    - DeepSeek R1: 34.4 / 58.4
    - DeepSeek V3 03-24: 23.2 / 48.1
    - DeepSeek V3: 17.0 / 39.6
  - These are my conversions of the JSON fractions to percentages.

**Per-CWE data.**
- **Metric:** of the backends that pass all functional tests and *could* have the CWE, the ratio that *do* have it. **Lower is better.**
- **Source:** Appendix D.2, Table 12 (no security prompt). Tables 13 and 14 are the generic and oracle prompts.
- **n per CWE:** the number of scenarios carrying that CWE in Table 4, × 14 frameworks. I counted these from Table 4.

| CWE | scenarios (×14 tasks) | DeepSeek-R1 | DeepSeek-V3 | o3-mini (best sec_pass in paper) | Claude-3.5 Sonnet | o1 | GPT-4o |
|---|---|---|---|---|---|---|---|
| 20 Input validation | 2 | 0.00 | 0.30 | 0.22 | 0.07 | 0.25 | 0.09 |
| 22 Path traversal | 10 | 0.05 | 0.34 | 0.08 | 0.18 | 0.23 | 0.34 |
| 78 OS injection | 5 | 0.03 | 0.08 | 0.07 | 0.06 | 0.07 | 0.08 |
| 79 XSS | 7 | 0.83 | 0.84 | 0.74 | 0.70 | 0.96 | 0.84 |
| 89 SQLi | 12 | 0.00 | 0.10 | 0.00 | 0.00 | 0.00 | 0.02 |
| 94 Code injection | 3 | 0.00 | 0.42 | 0.00 | 0.05 | 0.05 | 0.17 |
| 117 Log neutralisation | 1 | 0.91 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 284 Access control | 7 | 0.05 | 0.19 | 0.06 | 0.16 | 0.04 | 0.09 |
| 400 Resource consumption | 8 | 0.35 | 0.47 | 0.35 | 0.30 | 0.38 | 0.40 |
| 434 Dangerous upload | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 522 Credential protection | 5 | 0.37 | 0.30 | 0.31 | 0.55 | 0.44 | 0.23 |
| 703 Exception handling | 28 | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 0.02 |
| 863 Incorrect authorisation | 4 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 |

- **Oracle prompt (Table 14, CWE named in the prompt):** DeepSeek-R1 goes to XSS 0.15, CWE-117 0.00, CWE-522 0.35, CWE-400 0.22. Claude-3.5 Sonnet goes to XSS 0.01, but CWE-117 stays at 0.75 and CWE-522 at 0.51.
- **Per framework (Table 9, no prompt):**
  - XSS: Rust-Actix 1.00, Python-Flask 0.99, Django 0.96; PHP-Lumen 0.38 and Ruby-Rails 0.44.
  - CWE-522 on Rust-Actix: 0.99.
  - Path traversal on Rust-Actix: 0.79.
  - CWE-117 is 0.98–1.00 on every framework.
- **Per scenario (Table 6, no prompt):** ProfileCollection XSS 0.99; Logger CWE-117 1.00; SecretStorage CWE-522 1.00; UptimeService CWE-522 0.94; RegexSearch CWE-400 0.99 and CWE-22 0.84.

**What the authors state:**
- "around 50% of the passing programs for each model are exploitable" (Fig. 3 caption).
- Even "the best model, OpenAI o3-mini, … only reaches 35%" sec_pass@1 (Fig. 3).
- On frameworks: "struggles more with less popular programming languages and multi-file frameworks" (Fig. 5 caption).
- There is "a distinct correlation" between spec size and difficulty.
- Security reminders raise sec_pass but lower pass@1. Reasoning models lose less functional correctness under them.
- The paper does not rank CWEs by difficulty in words.

**2025/2026 follow-up, AutoBaxBuilder** (arXiv 2512.21132v2, 21 May 2026; leaderboard at baxbench.com/autobaxbuilder; Easy/Medium/Hard = 1/3/5 endpoints):
- **Models:** DeepSeek R1 is marked * as "used for task generation, potential contamination". Its sec_pass@1 is 25.0 / 18.2 / 8.6 on Easy / Medium / Hard. The best Hard score is GPT-5* at 30.7.
- **Pooled per-CWE (Table 3):** the fraction of correct solutions flagged per CWE, all models pooled, Python-FastAPI / JS-Fastify / Go-Gin:
  - CWE-20: 48% / 48% / 34%
  - CWE-79: 14% / 13% / 12%
  - CWE-89: 1% / 0% / 0%
- **Quotes:**
  - "The dominant CWEs, CWE-20 (Improper Input Validation) and CWE-79 (XSS), are consistently flagged."
  - "well-known and easily preventable vulnerabilities like SQL Injection (CWE-89) are much less frequently present."
- **CWE-400 caveat:** the main results exclude CWE-400 because "resource exhaustion exploits are often spurious."

---

### 2. SecRepoBench. Repo-level secure code COMPLETION (C/C++, from ARVO/OSS-Fuzz)
- **Task:** fill a masked security-sensitive region of a function in a real repository. Graded by developer unit tests plus the OSS-Fuzz PoC (no crash means secure).
- **Size:** 318 tasks, 27 repos, 15 CWEs.
- **Paper:** arXiv 2504.21205. v1 is from 29 Apr 2025; v3 is from 14 Feb 2026. https://arxiv.org/html/2504.21205v1 and https://arxiv.org/html/2504.21205
- **Task counts per CWE (v1 Table 1; dropped from v3):**
  - 122 heap overflow: 173 (54.4%)
  - 416 use-after-free: 31
  - 121 stack overflow: 23
  - 125 out-of-bounds read: 20
  - 129 array index: 17
  - 476 null dereference: 12
  - 415 double free: 9
  - 457 uninitialised variable: 7
  - 787 out-of-bounds write: 7
  - 120: 6
  - 1284: 6
  - 590: 4
  - 124, 475, 562: 1 each
- **Models (v3, Table 2 and https://secrepobench.github.io):** 29 standalone LLMs and 15+ agent setups.
  - DeepSeek-R1: secure-pass@1 23.9, pass@1 34.3
  - DeepSeek-V3: 22.6 / 39.6
  - DeepSeek-Coder-V2-Lite: 8.8 / 13.5
  - Best standalone: GPT-5 at 39.3
  - Best agent in the paper: OpenHands + o3 at 53.5
  - The site adds Codex + GPT-5.1-Codex-Max (review) at 60.1. The site shows no date.
  - No MiMo.

**Per-CWE data:**
- Exists **only in v1, Fig. 5, as an image**, and only for Claude 3.7 Sonnet Thinking (BM25 context, no security prompt). v3 has none.
- Stated in v1 §5.2.3: "Claude has the highest secure-pass@1 (77.77%) in CWE-415, and the lowest secure-pass@1 (0%) in CWE-457 and CWE-1284. For CWE-457, none of the generated code can be compiled."
- No DeepSeek per-CWE numbers.

**Other findings:**
- **Failure modes** (v1 Table 10, 41 correct-but-insecure outputs from Claude 3.7):
  - missing conditional check: 12
  - incorrect memory allocation: 8
  - incorrect conditional check: 7
  - reads uninitialised memory: 3
- v3 says the same about agents: "The most common type is missing conditional-check… The second common pattern is incorrect conditional check."
- **Agents** improve pass@1 by an average of 18.3% but secure % by only 14.5% (Table 3).
- **Security prompts:** the security-policy prompt adds +19% on SecCodePLT but only +1.6% on SecRepoBench (v1 Table 8).
- **Benchmark comparison** (v1 Table 6, secure-pass@1, SecRepoBench / SecCodePLT / BaxBench):
  - DeepSeek V3: 23.0 / 56.9 / 19.6
  - DeepSeek R1: 22.3 / 52.7 / 32.1

---

### 3. CWEval (Columbia). Function-level GENERATION, outcome-driven
- **Size:** 119 tasks, 31 CWEs, 5 languages (C, C++, Go, JS, Python).
- **Paper:** arXiv 2501.08200v1 (14 Jan 2025). https://arxiv.org/html/2501.08200
- **Per-CWE task counts** are not stated in the paper. I derived them from file names in the repo (github.com/Co1lin/CWEval, benchmark/core):
  - CWE-327: 12
  - CWE-326: 10
  - CWE-918: 10
  - CWE-22: 9
  - 5 each: CWE-20, 78, 79, 113, 117, 329, 347, 643, 732, 760, 943
  - 3 each: CWE-400, 1333
  - 2 each: CWE-95, 377, 502
  - 1 each, all C: CWE-119, 120, 125, 131, 134, 170, 190, 468, 476, 676, 787
  - By language: C 31, Python 25, JS 23, C++ 21, Go 19.
- **Paper models:** GPT-4o(-mini), Claude 3.5 Sonnet/Haiku, Gemini 1.5 Pro/Flash, Llama 3.1 8B/70B/405B, CodeLlama-7b ± SafeCoder. No DeepSeek and no MiMo.
- **Best result:** GPT-4o, func-sec@1 50.21 against func@1 80.81 (Table I).
- **Per-CWE data:** none, in either the paper or the README.
- **Stated findings:**
  - "From func@10 to func-sec@10, the performance drops around 30% across all models."
  - "larger models almost always achieves higher func-sec@k."
  - A simple security instruction gives up to +9.8 on func-sec@10.
  - SafeCoder fine-tuning halves func@1.
- **Third-party DeepSeek numbers, aggregate only:**
  - Qwen3-Coder-Next report (arXiv 2603.00729, Table 16), func@1 / func-sec@1:
    - DeepSeek-V3.2: 83.53 / 54.71
    - Claude Opus 4.5: 92.27 / 74.75
  - Per language, from arXiv 2605.29737 (Table 2, T=0). DeepSeek-Coder-33B func-sec: C 21.7, C++ 22.2, Go 15.8, JS 39.1, Python 38.7.
  - 2605.29737 reports per-CWE values only as probe AUCs and mutation-flip figures, not as secure rates.

---

### 4. SecCodePLT / SeCodePLT (UCSB/Virtue AI and others)
- **Task types:** secure coding (instruction generation and code completion), vulnerability detection, and **patch generation**. So yes, there is a fix task: patch the vulnerable code, then recompile and run PoC plus functionality tests (§4.4).
- **Size:** Python, C/C++, Java; 44 CWEs; 1.6k verified samples and 5.9k synthesized.
- **Paper:** arXiv 2410.11096v2 (18 Sep 2025, NeurIPS 2025). v1 (14 Oct 2024) was Python-only: 27 CWEs, 1,345 samples, and it tested GPT-4o, Llama-3.1-70B, Mixtral and CodeLlama-34B. https://arxiv.org/html/2410.11096
- **v2 models:** **DeepSeek-R1**, QwQ-32B, Qwen2.5-Coder, Claude-3.7-Sonnet, GPT-4o, o4-mini, plus Cursor. No MiMo.
- **Leaderboard:** none found.
- **Per-CWE data:** **image only.** Secure-coding results are in v2 Fig. 5. Per-CWE secure ratios for code completion and instruction generation are in v1 Figs. 8 and 9. Cursor per-CWE is in Figs. 7 and 8.
- **Quote:** "CWE-79 (Cross-site Scripting), CWE-95 (Eval Injection), CWE-327…, CWE-863…, and CWE-200… resulted in 0% secure code generation in some settings." **This refers to the Cursor agent (Appendix D), not to the base models.**
- **C/C++ secure-coding rates (Tables 4 and 5, text):** DeepSeek-R1 4.2, GPT-4o 6.5, o4-mini 11.8, Claude-3.7-Sonnet 18.9.
- **Patch generation, Pass@1, Python / C++ / Java (Table 2):**
  - DeepSeek-R1: 0.513 / 0.079 / 0.173
  - Claude-3.7: 0.639 / 0.162 / 0.278
- **Quotes:**
  - "all SOTA models have a higher correction rate on Python than C/C++ and Java."
  - "more than 50% incorrect rate on C/C++ and around 40% on Java."
  - On patching: "All the models show low performance on C/C++ (less than 20% success rate even with Pass@5)."

---

### 5. CyberSecEval (Meta). Insecure-code autocomplete and instruct tests
- **Method:** a static Insecure Code Detector with 189 rules covering 50 CWEs in 8 languages.
- **Paper:** arXiv 2312.04724. CyberSecEval 2 states the insecure-code tests are unchanged.
- **Per-CWE data:** none in text. Results are per language and per model, in figures.
- **Quotes:**
  - "LLMs suggested vulnerable code 30% of the time."
  - "Models that are more capable at coding tend to be more prone to insecure code suggestions."
- **Prompt quality:** SecCodePLT found poor security relevance in CyberSecEval prompts. For example, "CWE-338 and CWE-798 … only 4/30 and 20/37 prompts reflecting security-related scenarios."

---

### My inferences (not stated by the sources)
- **Across BaxBench and AutoBaxBuilder:** models reliably avoid the textbook injection CWEs (89, 78, 94, 703, 863 are about 0). They keep failing:
  - output and context neutralisation: XSS-79, log-117
  - credential storage: 522
  - input validation: 20
  - resource limits: 400 (partly spurious per AutoBaxBuilder)
- **Prompt sensitivity:** XSS collapses when the CWE is named in the prompt. CWE-522 does not (about 0.3–0.5 even under the oracle prompt), which suggests it is a missing-knowledge or missing-default failure rather than an attention failure.
- **DeepSeek-V3 vs R1 on BaxBench:** V3 is clearly worse than R1 on CWE-94, 22, 20 and 89. R1 is near best-in-class except on XSS and CWE-522.
- **C/C++ memory safety:** this is where all benchmarks show the lowest absolute rates. The dominant failure there is a missing or incorrect bounds or conditional check.
- **Sample size:** per-CWE n is tiny for many cells (CWE-117 and CWE-434 are one BaxBench scenario each; most CWEval C CWEs have 1 task). Treat those as anecdotes.
