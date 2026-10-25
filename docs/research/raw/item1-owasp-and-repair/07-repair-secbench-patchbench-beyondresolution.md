<!-- Verbatim final report of a research sub-agent (id ae407e91d97e1270e), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

## Summary
Only SEC-bench has per-instance repair results that can be broken down by vulnerability class, so the per-class and per-CWE tables for it are my own computation. None of the three papers publishes a per-CWE repair success table. PatchBench publishes the CWE label of each task but no per-instance agent results. "Beyond Resolution Rates" is SWE-bench Verified (Python), not a security benchmark. No DeepSeek or Xiaomi MiMo results appear in any of the three sources, or in the SEC-bench leaderboards.

---

## 1. SEC-bench (arXiv 2506.11791, v2 22 Oct 2025)
**Sources:** https://arxiv.org/html/2506.11791v2 · leaderboard https://sec-bench.github.io · run logs https://github.com/SEC-bench/experiments · dataset https://huggingface.co/datasets/SEC-bench/SEC-bench

- **Task type:** real CVEs and OSS-Fuzz bugs in C/C++. Two tasks: PoC generation and patching. A patch is graded by the PoC no longer triggering the sanitizer. Tasks come from 29 projects.
- **Size:** 200 verified instances in the paper (the `cve` split). The HF `eval` split has 300 (the `cve` 200 plus 100 from `oss`).
- **Gold patch size (Table 2, Sec 2.6), mean / max:** 17.3 / 650 lines, 1.3 / 11 files, 1.6 / 11 functions.
- **Models in the paper:** SWE-agent, OpenHands and Aider, run with Claude 3.7 Sonnet, GPT-4o and o3-mini. Table 5 also uses Claude 3 Haiku. No DeepSeek or MiMo.
- **Headline patch results:**
  - OpenHands + Claude 3.7 Sonnet: 34.0% on 200 (Sec 3.2).
  - SWE-agent: 33.8% on the 80-instance subset.
  - Table 4 (80 instances): its cell values did not extract from the HTML.
- **Leaderboard patch results:** AgenticRepair + GPT-5.2 75%, AgenticRepair + GPT-5-mini 50%, OH-Sonnet 34%, SWEA-Sonnet 31.5%, Aider-Sonnet 23.5%.
  - The two 2026-01 rows come from Univ. Melbourne. Their metadata.yaml calls them "AgentMem" and marks them `verified: false`.
- **Per-CWE data in the paper:** none.
  - Appendix A gives only a CWE distribution, as an image (Figure 3).
  - Quotes: "CWE-125 (Out-of-bounds Read) and CWE-787 (Out-of-bounds Write) are highly frequent"; "CWE-476 (NULL Pointer Dereference) is also prominent"; "CWE-416 (Use After Free) is another significant critical vulnerability type."
  - There is no stated finding on which CWE is hardest to fix.
- **Stated difficulty factors:**
  - Failure categories (Sec 3.3): "SV happens when agents misidentify the root cause of a vulnerability"; "CE occurs when patches introduce defects like mismatched types or pointer dereference errors"; "IF arises when agents generate excessively large patches due to iterative attempts"; IF is "62.18% of [OpenHands'] total failures".
  - Appendix F.1: agents "often misidentify vulnerability locations".
  - Case example: in mruby.cve-2022-1201 the agent picked one file while the gold patch touches three.
- **SEC-bench Pro (arXiv 2605.26548; leaderboard, June 2026):** PoC generation only (344 tasks in V8, SpiderMonkey and Linux), no patching and no per-CWE data, so it is not relevant to repair. Its open-weight rows are GLM-5 3.8%, Kimi K2.5 2.3% and MiniMax M2.5 0.6%. No DeepSeek or MiMo.

### MY COMPUTATION (not published numbers)
**Inputs:**
- Per-instance results from `evaluation/Patch/<run>/report.jsonl`, stored in Git LFS, fetched via `https://media.githubusercontent.com/media/SEC-bench/experiments/main/evaluation/Patch/<run>/report.jsonl`.
- Runs: oh_sonnet, swea_sonnet, aider_sonnet (200 instances each); agenticrepair_gpt-5.2, agenticrepair_gpt-5-mini, smola_gpt-5.2, smola_gpt-5-mini (300 each).
- My totals match the leaderboard exactly on the 200-instance split: 68/200, 63/200, 47/200, 150/200 and 100/200.
- Crash class: parsed from the `sanitizer_report` field of the HF dataset. I split SEGV at fault address < 0x10000, which is roughly a null dereference.
- CWE: looked up per CVE in the NVD API (NVD Primary CWE, else the first CWE listed). 20 of the 200 instances have more than one CWE listed.

**Table A. Patch success by sanitizer crash class (200-instance `cve` split)**

| Class | n | OH+Son3.7 | SWEA+Son3.7 | Aider+Son3.7 | AgentRepair+GPT-5.2 | AgentRepair+5-mini | Smol+GPT-5.2 | Smol+5-mini |
|---|---|---|---|---|---|---|---|---|
| heap-buffer-overflow | 74 | 32% | 30% | 23% | 78% | 57% | 47% | 42% |
| SEGV near-null | 53 | 30% | 40% | 23% | 83% | 55% | 53% | 36% |
| SEGV other address | 18 | 50% | 22% | 11% | 67% | 39% | 44% | 28% |
| heap-use-after-free | 17 | 29% | 12% | 12% | 59% | 24% | 18% | 12% |
| memory leak (LSan) | 13 | 54% | 38% | 38% | 69% | 38% | 23% | 23% |
| stack-buffer over/underflow | 12 | 42% | 42% | 25% | 67% | 58% | 75% | 50% |
| double-free / bad-free | 3 | 0% | 0% | 0% | 33% | 0% | 33% | 0% |
| ALL | 200 | 34.0% | 31.5% | 23.5% | 75.0% | 50.0% | 45.0% | 34.5% |

**Same breakdown on the 300-instance split (the four 2026 runs; n per class in brackets):**
- heap-buffer-overflow (114): 75 / 52 / 46 / 39%
- heap-use-after-free (42): 67 / 31 / 45 / 21%
- SEGV near-null (56): 82 / 55 / 54 / 36%
- global-buffer-overflow (7): 29 / 29 / 14 / 29%
- double-free / bad-free (5): 20 / 0 / 20 / 0%
- stack-buffer over/underflow (17): 71 / 65 / 71 / 53%

**Table B. Patch success by NVD CWE (200-instance split; rows with n ≥ 5)**

| CWE | n | OH | SWEA | Aider | AR-5.2 | AR-mini | Smol-5.2 | Smol-mini |
|---|---|---|---|---|---|---|---|---|
| CWE-787 | 46 | 28% | 26% | 22% | 74% | 61% | 50% | 43% |
| CWE-125 | 45 | 44% | 40% | 24% | 84% | 60% | 53% | 42% |
| CWE-476 | 33 | 27% | 42% | 24% | 79% | 52% | 58% | 52% |
| CWE-416 | 21 | 33% | 19% | 19% | 52% | 29% | 29% | 5% |
| CWE-119 | 9 | 11% | 11% | 0% | 67% | 22% | 33% | 11% |
| CWE-122 | 8 | 25% | 50% | 12% | 100% | 50% | 50% | 25% |
| CWE-401 | 7 | 14% | 14% | 29% | 86% | 43% | 43% | 43% |
| CWE-772 | 7 | 86% | 57% | 43% | 57% | 29% | 0% | 0% |
| NVD-noinfo | 6 | 67% | 0% | 17% | 67% | 17% | 0% | 0% |
| CWE-190 | 5 | 40% | 40% | 80% | 80% | 40% | 20% | 0% |

**My inferences:**
- Use-after-free (CWE-416 / heap-UAF) is the lowest of the large classes for every 2026 run, and for 6 of 7 runs by CWE. Its gap below the overall rate is 16 to 30 points.
- Double-free and bad-free are near zero, but n is only 3 to 5.
- CWE-125 (OOB read) and near-null SEGV / CWE-476 are the easiest.
- 40 of 300 instances were never solved by any of the 7 runs: 14 heap-buffer-overflow, 7 heap-UAF, 5 global-buffer-overflow, 5 SEGV-other, 4 double-free / bad-free, 3 SEGV near-null, 1 stack-buffer over/underflow, 1 stack-use-after-return.
- Gold-fix size (300-instance split, AR-5.2 / AR-mini / Smol-5.2 / Smol-mini):
  - 1 file: 75 / 49 / 46 / 34%. 2+ files: 63 / 42 / 40 / 31%.
  - More than 20 changed lines: 66 / 38 / 36 / 21%, against 72 to 80% for small fixes on AR-5.2.
  - So larger, multi-file fixes are somewhat harder, but the effect is modest.
- Caveats:
  - Small n: the standard error is about 7 to 10 points at n = 20 to 50.
  - PoC-only grading inflates these rates (see PatchBench below).
  - The 2026 runs are self-reported and unverified.

---

## 2. PatchBench (arXiv 2609.04075, 3 Sep 2026)
**Sources:** https://arxiv.org/html/2609.04075v1 · repo https://github.com/ai-sec-lab/PatchBench · HF https://huggingface.co/datasets/ai-sec-lab/PatchBench

- **Task type:** real ARVO / OSS-Fuzz C/C++ vulnerabilities.
  - Only tasks whose developer fix lies off the crash stack are kept (trace-overlap Jaccard ≤ 1/2).
  - Each bug is transplanted into a newer version of its project and mutated with NatGen and CodeMorph.
  - Grading: extra PoCs from directed fuzzing, a sanitizer regression check, an output-state check and unit tests.
- **Size:** 213 tasks from 32 projects, across 16 CWEs (Sec 4.1).
- **Models (Table 2, "Solved" %):**
  - Codex + GPT-5.6 Sol 59.2
  - OpenHands + GPT-5.6 Sol 58.2
  - Claude Code + Opus 4.8 56.8
  - Atlantis 48.4
  - OpenHands + Opus 4.8 47.9
  - OpenHands + Gemini 3.5 Flash 44.1
  - Buttercup 42.7
  - OpenHands + GPT-5 42.3
  - OpenHands + Sonnet 4.5 38.0
  - OpenHands + Gemini 3.1 Pro 31.5
  - RoboDuck 29.6
  - No DeepSeek or MiMo.
  - PoC-pass rates in the same table run from 46.5% to 98.1%. The average is 83.1% PoC-pass against 45.3% solved, which is the paper's "1.83×" inflation.
  - 67 of 213 tasks are unsolved by all 11 agents.
- **Per-CWE results: none published.** The repo has no per-instance agent results, only task data.
- **MY COMPUTATION, task distribution only (no success rates):** from the `CWE_ID` field of `data/metadata.json` (https://raw.githubusercontent.com/ai-sec-lab/PatchBench/main/data/metadata.json).
  - Primary CWEs: CWE-126 85, CWE-416 50, CWE-122 14, CWE-415 13, CWE-787 12, CWE-843 9, CWE-1284 9, CWE-127 7, CWE-476 4, CWE-824 3, CWE-758 2, and 1 each of CWE-252, 590, 617, 562, 763.
  - Crash types: heap-buffer-overflow 73, heap-UAF 42, SEGV 43 (34 ASan, 9 UBSan), double-free 13, global-buffer-overflow 11, use-after-poison 8, other 23.
- **Stated findings on difficulty (no per-CWE ranking):**
  - "81% of Codex + GPT-5.6 Sol's patches modify functions on the crash stack trace" (Sec 2.2).
  - On 92 tasks whose developer fix is off the stack, 64% of agent patches still modify crash-stack functions while passing the PoC.
  - Failure pattern 1 (Sec 5.3), "Agents guard the symptom with incomplete local checks", is "the most common failure pattern". It covers 41/81 Codex, 47/87 Claude Code and 39/72 OpenHands + Gemini 3.5 Flash patches that pass the PoC but fail validation.
  - Other patterns: "fail to localize the vulnerability that causes malformed functionality"; "silences the crash by deleting the offending operation"; "add broader conditions that reject benign inputs".
  - Budget: "budget is not what holds the agents back" (Codex 59.2% at $5, 61.5% at $15).
  - AIxCC systems "perform worse than general-purpose agents on the same model."
  - Memorisation on SEC-bench (Sec 3.3): about 25% of repository-level agent patches have DiffBLEU > 0.75 against the historical fix, against 11% for local-context patching. Per pair: GPT-5.6 Sol 8.3% → Codex 22.0%; Opus 4.8 10.7% → Claude Code 27.7%; Gemini 3.5 Flash 13.0% → OpenHands 24.3%.
  - Fix size and files touched are not analysed.

---

## 3. "Beyond Resolution Rates" (arXiv 2604.02547, 2 Apr 2026)
**Source:** https://arxiv.org/html/2604.02547v1 (supplement: Zenodo DOI 10.5281/zenodo.19351830)

- **Not a security benchmark.** It covers SWE-bench Verified: 500 Python tasks from 12 repos, with 9,374 trajectories from 19 agents (8 frameworks, 14 LLMs). The paper never mentions security, vulnerabilities or CWEs. **No per-CWE data.**
- **Models:** Claude 3-Opus through Opus 4.5, GPT-4, GPT-4o, GPT-5, Kimi-K2, Doubao-seed-code, Devstral-small, Qwen-32B and lm-32b. Rates range from 15.1% to 79.2% (Table 6). No DeepSeek or MiMo.
- **Difficulty findings, which do transfer to repair in general:**
  - 55 tasks (11%) were never solved. 12 of them need simple patches, and humans annotated them "<15 min" or "15 min–1 hr".
  - Patch complexity of those 12 is "statistically indistinguishable" from always-solved tasks (mean 4.75 vs 3.76 changes, p = 0.24).
  - "No patch or metadata feature is significant." Only test-demand features are, for example fail-to-pass count δ = +0.61, p < 0.001.
  - Agents "intervene at the wrong architectural layer (10/12 tasks)", even though the best agent found the gold file in 12/12.
  - Failures come from "gaps in architectural reasoning and domain knowledge."
  - Within a task, longer trajectories go with success: resolved runs were longer on 263 of 416 tasks, p = 1.9e-9.

---

## Stated vs inferred
- **Stated:** every number in the plain sections above, with its URL and table or section.
- **Inferred:** only the "MY COMPUTATION" blocks, which are SEC-bench Tables A and B, the fix-size split, the never-solved list, and the PatchBench CWE counts. My scripts and intermediate data are in the session scratchpad under `secb/` and `scripts/`, not in the repo.
