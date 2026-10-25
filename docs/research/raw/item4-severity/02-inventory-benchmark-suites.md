<!-- Verbatim final report of a research sub-agent (id af719d5fc507ca9f7), saved 2026-10-16 from the session transcript. Model output: verify against cited sources. -->

## Vulnerability-repair benchmark inventory (2026-10-16)

I did all the work myself with web and curl; no sub-agents.

**Bottom line:** five sources give task→CVE plus per-task, per-model pass/fail right now, and all five are downloaded:
- **LiveCVEBench**: 31 model×agent runs on 190 CVEs from 2025.
- **PatchEval**: 9 directly prompted LLMs on 230 CVEs.
- **BountyBench**: 10 agents on 40 CVEs.
- **SEC-bench**: 7 patch runs on 200 CVEs plus 100 OSS-Fuzz tasks.
- **Gatti cve-bench**: 7 models on 19 CVEs plus 1 GHSA.

DeepSeek is covered in LiveCVEBench, PatchEval and BountyBench. Xiaomi MiMo appears nowhere.

Everything is in `/Users/dev/.tb-graders/cwe/research-raw/item4-severity/benchmarks/` (101 MB in total). Provenance for every file is in `SOURCES.txt` there.

### Per-benchmark rows

**1. LiveCVEBench / CVE-Factory** (arXiv 2602.03012)
- **Size and languages:** 190 tasks, 14 languages, 153 repositories. All tasks are 2025 CVEs and the task folders are named by CVE ID.
- **Availability:** tasks are public at https://github.com/livecvebench/LiveCVEBench-Preview (MIT), including LiveCVEBench-verified (183) and PatchEval-verified (204). The harness is public at https://github.com/livecvebench/CVE-Factory (README says MIT; there is no licence file).
- **CVE mapping:** yes, direct.
- **Per-task results:** yes. https://github.com/livecvebench/livecvebench.github.io/blob/master/data/leaderboard.json, at `results.user_report[]`, gives `{model, agent, cve_results{CVE:{success, turns, tokens}}}`.
  - It has 31 runs: 8 models × Mini-SWE-Agent, OpenHands and Terminus-2, plus Claude Code for Opus 4.5 and Sonnet 4.5, plus Abacus-CVE.
  - **DeepSeek V3.1-Terminus and DeepSeek V3.2** are included. Other models: MiniMax M2, GLM-4.6, Qwen3-Coder-480B, GPT-5.1-Codex, Gemini 3 Pro, Claude Sonnet 4/4.5, Opus 4.5.
  - `data/merged_results_v5..v34.json` (27 versions) are earlier snapshots.
- **Transcripts:** I found none for the benchmark runs. https://huggingface.co/datasets/Luoberta/cve_train holds training traces, not benchmark runs.
- **Notes:**
  - DeepSeek V3.2 and Qwen under OpenHands pass only 4 of 190, which looks like a harness failure.
  - The paper's table (`data/experiment_table.md`) does not match the leaderboard.json counts (e.g. OpenHands + Opus 4.5 is 25.44% vs 58/190). Which one is final is unverified.
  - All runs are self-reported by the authors.
- **Downloaded:** `livecvebench/site-data/` (20 MB). Includes `leaderboard.json` (752 KB), `cve_tasks_summary.json` and `cve_publish_dates.json`.

**2. PatchEval** (arXiv 2511.11019; https://github.com/bytedance/PatchEval, Apache-2.0)
- **Size and languages:** 1,000 CVEs; 230 have runtime environments. Go, JavaScript, Python.
- **CVE mapping:** yes, the key is the CVE ID.
- **Per-task results:**
  - **Directly prompted LLMs: yes.** `patcheval/log/llm/fixed_*_Default.json` has per-CVE, per-epoch `poc_status`, `unittest_status` and `status`. Models: **DeepSeek-V3, DeepSeek-R1-0528**, Doubao-1.6 and 1.6-thinking, Gemini-2.5-pro, GPT-4.1, Kimi-K2, Qwen3-Coder-480B, Qwen3-Max.
  - **Agents: patches only, no verdicts.** `patcheval/log/agent/{sweagent,openhands,claudecode}/*.jsonl` holds `{cve, fix_patch}` for SWE-agent, OpenHands and Claude Code with DeepSeek-R1, DeepSeek-V3 (SWE-agent only), Doubao, Gemini and GPT-4.1.
  - The leaderboard (https://patcheval.github.io) is aggregate only and lists 33 entries, including DeepSeek V3.2 Thinking/Speciale, GPT-5 and Doubao-Seed-1.8, which have no logs.
  - https://github.com/PatchEval/experiments contains only a README.
- **Transcripts:** none. The raw LLM logs are 240 MB and include generated code.
- **Notes:**
  - "Epochs" are iterative retries. Status is None on epoch 1 for about 50 CVEs per model.
  - A CVE solved in any epoch reproduces DeepSeek V3's leaderboard score (52/230 vs 23.04%) but not the others (R1 is 41% vs 20.43%). The scoring rule is unverified.
- **Downloaded:** `patcheval/compact_llm/` (9 files, about 2.7 MB) and `raw/agent_patches/` (17 files, 52 MB).

**3. BountyBench** (arXiv 2505.15216v3)
- **Size and languages:** 40 bounties in 25 systems, mostly Python and JavaScript web apps.
- **Availability:** code at https://github.com/bountybench/bountybench and tasks at https://github.com/bountybench/bountytasks (both Apache-2.0).
- **CVE mapping:** yes. Paper Table 20 gives CVE, CVSS and CWE for all 40 bounties.
- **Per-task results:** yes, for 10 agents (Tables 25 and 26), where success means solved within 3 attempts. Agents: Claude Code, Codex CLI o3-high and o4-mini, and C-Agent with o3-high, GPT-4.1, Gemini 2.5, Claude 3.7, Qwen3-235B, Llama 4 Maverick and **DeepSeek-R1**.
- **Transcripts:** the paper says logs are at bountybench.github.io, which **returns 404**. I found no other location.
- **Notes:** after parsing, Claude Code shows 34 successes against the table's "Total 35"; there is one cell I could not reconcile.
- **Downloaded:** `bountybench/bountybench_patch_long.tsv` (400 rows: task, agent, success, CVE, CVSS, CWE, bounty), the `table*.tsv` files and the paper HTML.

**4. SEC-bench** (arXiv 2506.11791)
- **Size and languages:** 200 CVE instances (`eval-cve`) plus 100 OSS-Fuzz instances (`eval-oss`). C/C++.
- **Availability:** HF https://huggingface.co/datasets/SEC-bench/SEC-bench (MIT). Experiments at https://github.com/SEC-bench/experiments (Apache-2.0).
- **CVE mapping:** yes for the 200, through the instance_id (e.g. `njs.cve-2022-32414`). The OSS-Fuzz 100 have no CVE.
- **Per-task results:** `evaluation/{Patch,PoC}/<run>/report.jsonl`. These are **git-LFS files, about 420 MB in total**, because they embed patches and logs.
  - Patch runs: SWE-agent, OpenHands and Aider with Claude 3.7 Sonnet (200 tasks, marked verified).
  - Newer runs (Jan to Mar 2026, unverified, self-reported by Univ. Melbourne): AgenticRepair/AgentMem and Smolagents with GPT-5.2 and GPT-5-mini (300 tasks).
  - No DeepSeek. There are no newer runs or PRs after 2026-03-26.
- **Transcripts:** the newer runs have `logs/` and `trajs/`. The logs dirs are about 1.5 GB (smola gpt-5-mini 817 MB, smola gpt-5.2 603 MB, agenticrepair about 36 MB each). Trajectories are LFS objects of unknown total size. Sonnet runs have only the `logs` field inside report.jsonl.
- **Downloaded:** `sec-bench/compact/` (10 runs × instance, success, reason; 600 KB), `dataset/eval-cve.jsonl` and `eval-oss.jsonl`, and one full raw report.

**5. Gatti "CVE-Bench" 2026** (https://github.com/GiovanniGatti/cve-bench, MIT; blog https://giovannigatti.github.io/cve-bench/)
- **Size and languages:** 20 Python tasks (19 CVEs plus GHSA-r758-8hxw-4845), CVSS 2.1 to 9.8.
- **Runs:** 3 prompt conditions × gpt-5.5, gpt-5.4-mini, gpt-5.4-nano, laguna-m.1 and laguna-xs.2, plus partial runs of Claude Haiku 4.5 (38) and Sonnet 4.6 (2). No DeepSeek.
- **Transcripts:** full agent turns are in `results/*.json` (about 378 MB; not downloaded).
- **Downloaded:** `gatti-cve-bench/runs.jsonl` (340 runs, 217 KB) with `solved_author_rule`. This applies the author's rule from `generate_charts.py` and reproduces the blog numbers (gpt-5.5 30/60, laguna-xs.2 20/60).

**6. CyberGym** (arXiv 2506.02548)
- This is PoC generation, not repair, so it is out of scope. Tasks use ARVO and OSS-Fuzz IDs.
- The leaderboard is aggregate only: https://www.cybergym.io/assets/data/cybergym.json.

**7. CyberGym-E2E** (arXiv 2606.04460; https://github.com/sunblaze-ucb/cybergym-e2e, Apache-2.0)
- **Size and languages:** 920 C/C++ tasks with IDs like `arvo:24101` and `oss-fuzz:447480433`.
- **CVE mapping:** no. Mapping would have to go through OSV OSS-Fuzz aliases, which are sparse.
- **Results:** the leaderboard JSON (https://www.cybergym.io/assets/data/cybergym-e2e.json, downloaded) is aggregate only. It includes Aegis + **DeepSeek-V4-Flash-0731** (ZJU).
- The Aegis write-up (https://github.com/bofeng17/Cybergym-E2E) mentions a per-task `results.json` and trajectories, but they are **not public**; submissions go by email.

**8. AutoPatchBench / CyberSecEval 4** (PurpleLlama, `CybersecurityBenchmarks/datasets/autopatch/`)
- 136 samples (113 in the lite set), C/C++, ARVO IDs with no CVE.
- I found no per-sample public results. Dead end.

**9. PatchBench** (arXiv 2609.04075; https://github.com/ai-sec-lab/PatchBench, MIT; HF ai-sec-lab/PatchBench)
- 213 tasks, C/C++, ARVO-numbered, CWE only.
- The vulnerabilities are transplanted and mutated, so a CVE join is not meaningful even though the site shows CVE-2022-1276 as an example.
- The leaderboard at https://patchbench.github.io is aggregate only: 11 agents including Atlantis, Buttercup and RoboDuck. No logs.
- Downloaded the metadata only.

**10. CWE-bench (Collinear)** (https://cwe-bench.com)
- 120 held-out tasks, private. Aggregate only; includes DeepSeek-V4.1-Flash and V4-Flash. Dead end.

**11. Vul4Py** (arXiv 2608.00692; https://github.com/tabudz/vul4py, no licence)
- 100 Python tasks (92 CVE plus 8 GHSA), listed in `dataset/vul4py.csv` (downloaded).
- The `results/` folder is empty, and the paper gives aggregates only (GPT-4o, Sonnet 4, OpenHands, Trae, SWE-agent, APPATCH).

**12. SecureAgentBench** (arXiv 2509.22097, now titled SecureVibeBench; https://github.com/iCSawyer/SecureVibeBench, MIT)
- 105 ARVO-based C/C++ tasks. This is secure code generation, not repair.
- Results are aggregate only (`assets/results.md`, includes DeepSeek-V3.1). Dead end.

**13. ZeroDayBench** (arXiv 2603.02297)
- 22 novel vulnerabilities ported from CVEs into other codebases, so no CVE identity.
- No code release beyond an anonymous mirror link; results by tier only. Dead end.

**14. AIxCC finalists (Atlantis, Buttercup, RoboDuck)**
- The challenges are mostly synthetic injected vulnerabilities.
- The per-challenge data page https://archive.aicyberchallenge.com/data/ says "Coming soon".
- Theori's traces (https://theori-io.github.io/aixcc-public/) are test traces, not scored outcomes. Dead end for now.

**Other:** the HF space FrontierAICybersecurity/Cybersecurity_leaderboard is aggregate only (2025-06).

### Ranking

**Usable now** (all downloaded):
1. LiveCVEBench: largest model grid, includes DeepSeek, 2025 CVEs.
2. PatchEval LLM logs: 9 models, includes DeepSeek, 230 CVEs. The epoch semantics need care.
3. SEC-bench: 7 patch runs, 200 CVEs, Sonnet 3.7 and GPT-5.x only.
4. BountyBench: 10 agents, includes DeepSeek-R1, with CVSS already attached. Only 40 tasks, and success is best of 3.
5. Gatti: 20 tasks, so small but clean.

**Need extra work:**
- **PatchEval agent runs:** re-grade the published patches with `patcheval/evaluation/run_evaluation.py` and their Docker images.
- **Vul4Py:** re-run, or ask the authors for `results/correct_<agent>.jsonl`.
- **CyberGym-E2E:** ask the Aegis team or the maintainers for per-task `results.json`. An ARVO/OSS-Fuzz→CVE mapping through OSV would still give sparse coverage.
- **BountyBench logs:** ask the authors, since the site is down.

**Dead ends:** CWE-bench, AutoPatchBench, PatchBench, SecureAgentBench, ZeroDayBench, CyberGym (not repair), and AIxCC (data not released).

Not verified: the LFS trajectory sizes for SEC-bench, and whether LiveCVEBench run transcripts exist anywhere.
