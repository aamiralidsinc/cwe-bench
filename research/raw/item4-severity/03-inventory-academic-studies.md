<!-- Verbatim final report of a research sub-agent (id a38b1dcaf1b617dd1), saved 2026-10-16 from the session transcript. Model output: verify against cited sources. -->

## Inventory of vulnerability-repair studies: which model fixed which CVE

I did this myself with web searches, arXiv/USENIX/ACL PDFs, the GitHub API, Zenodo and curl. I checked every table I extracted against totals stated in the paper. Data is in `/Users/dev/.tb-graders/cwe/research-raw/item4-severity/studies/`. No study evaluates Xiaomi MiMo. DeepSeek models are flagged below as **[DS]**.

### Ranked list

**A. Usable now: CVE IDs plus per-model pass/fail, extracted and checked**

1. **VulnRepairEval** (arXiv 2509.03331). Python, 23 CVEs, single attempt, success = the PoC exploit fails on the patched code.
   - **Table 2 is the full grid: 12 models, each with an F and an R column.** It adds DeepSeek V3 671B **[DS]**, GPT-4o, GPT-3.5, Gemini 2.0 Flash, Qwen3 8B and Qwen3 235B to the 6 models of the Table 6 you already have. DeepSeek R1 671B **[DS]** is in both.
   - The HTML version loses the empty cells, so I took glyph x-positions from the PDF with `pdftotext -bbox`.
   - Verification:
     - All 12 R-column totals equal Table 3 P_succ×23 (Gemini 2.5 Pro 5, R1 4, V3 3, Gemini 2.5 Flash 2, Gemini 2.0 Flash 2, Qwen3 235B Thinking 2, o4-mini 1, GPT-3.5 1, the rest 0).
     - The fixed sets agree cell by cell with Table 6 for the 6 shared models.
   - File: `vulnrepaireval/table2_12models_repair_format.tsv` (2.3 KB).
   - Code repo: github.com/WWILLV/VulnRepairEval, saved as `VulnRepairEval-main.tar.gz` (405 KB). It has the framework only: no PoCs, no patches, no results. The paper says "please contact the authors". The repo has no LICENSE file, although the README badge says MIT.

2. **APPATCH** (USENIX Security 2025). C, mostly Linux kernel, 97 CVEs from 2024 (76 zero-day plus 21 interprocedural); separate ExtractFix results were not extracted.
   - Models: GPT-4, Claude 3.5, Gemini 1.5, Llama 3.1, DeepSeek-Coder-V2 **[DS]**, CodeQwen 1.5, CodeLlama.
   - Source: Zenodo https://zenodo.org/records/14741018, CC-BY-4.0, `appatch.zip` 164 MB, downloaded. It holds the manual label of every generated patch in `results/<model>/**/*.res`, plus all prompts, reasoning traces and patches.
   - My TSV: `appatch/zeroday_per_sample_per_model.tsv` (97 rows, CVE from the filename; 1 = any patch labelled SynEq, SemEq or Plausible). The extracted `.res` files are in `appatch/res/`.
   - Checks that match the paper exactly: DeepSeek-Coder-V2 15/97, CodeQwen 18/97 and CodeLlama 2/97 (Table 9); all 4 large models on the interprocedural split (Table 12); Gemini 26/97 (Table 2).
   - **Unresolved mismatch** with Table 2: GPT-4 43 vs 38, Claude 49 vs 48, Llama 37 vs 34. Use those three columns with care.

3. **CWEFT** (ESEM 2026). Java (Vul4J), 42 CVEs × 4 prompt conditions × 3 models = 504 cells. Models: Claude Sonnet 4.5, Gemini 2.5 Pro, GPT-5.
   - Source: Zenodo 10.5281/zenodo.21672348, which resolves to record 21679413. CC-BY-4.0; the code inside is Apache-2.0. `cweft-EBFE.zip` (66 KB), unzipped.
   - `results/results.csv` gives per cell: CVE, CWE, compiled, pov_passed, regressions and an L0–L3 trust level.
   - My pivot `per_cve_L3_pivot.tsv` matches the package's `table_model_x_level.csv` exactly.
   - The README says the 504 per-call logs are archived on Zenodo, but the deposited zip does not contain them.

4. **SAN2PATCH** (USENIX Security 2025). C (VulnLoc), 39 bugs, 31 of them with a CVE.
   - `table3_per_model.tsv` covers GPT-4o, GPT-4o-mini, GPT-3.5, Claude 3.5 Sonnet, Gemini 1.5 Pro and Gemini 1.5 Flash. Totals 31/17/8/28/18/14 match the paper.
   - `table1_gpt4o_ablations_and_tools.tsv` covers GPT-4o prompting ablations plus VulnFix, ExtractFix, VulRepair and VulMaster. All 12 column totals match.
   - Artifacts: Zenodo 15614211 (current version 15710424; code and benchmark) and 15654492 (17-page supplement PDF), CC-BY-4.0. GitHub acorn421/san2patch and acorn421/san2patch-benchmark are MIT. All downloaded. They hold no generated patches or logs.

5. **Pearce et al.** (IEEE S&P 2023). C, 12 ExtractFix scenarios covering 11 CVEs. Models: code-cushman-001, code-davinci-001, code-davinci-002, j1-large, polycoder, gpt2-csrc.
   - Source: Zenodo 7199939, CC-BY-SA-4.0. The archive `Data.zip` is 11.1 GB, so I read only `final_results.csv` (29 MB), the diff HTML and the README out of it via HTTP range requests.
   - `realworld_per_cve_per_engine.tsv` gives 1 = any unique program passing the functional and security tests, plus counts.
   - Verification: the set of non-zero cells equals the set of engines listed per scenario in Table VII. Table VII marks some passing patches (EF08, EF15) as not reasonable.

6. **Wu et al.** (ISSTA 2023). Java, 50 CVEs (35 Vul4J plus 15 VJBench), each with a CVE ID.
   - `table5_per_vuln_per_model.tsv`: 13 techniques (Codex, CodeT5, CodeGen, PLBART, InCoder, four fine-tuned variants, CURE, Recoder, RewardRepair, KNOD). 1 = manually judged correct.
   - All column totals match Table 5 and Table 4. Rows not listed in Table 5 are set to 0. The Codex column is the union over 25 runs.
   - Repo: github.com/lin-tan/llm-vul, BSD-3-Clause, `llm-vul-main.tar.gz` 49 MB. It includes `Model_patches/model_output` with per-patch test results. I kept the tarball and deleted the 547 MB extracted copy.

7. **Garg et al.** (arXiv 2511.23408). Java, 15 real vulnerabilities (13 with a CVE ID, plus APACHE-COMMONS-001 and HTTPCLIENT-1803) and 41 injected variants. 14 models, including DeepSeek-R1-Distill-Qwen-32B **[DS]**.
   - `table2_per_vuln_per_model.tsv`: the real and artificial totals for every model match Table 3 exactly.
   - Paper only: no artifact link, no patches.

**B. Usable but needs extra work**

8. **PatchAgent** (USENIX Security 2025). C/C++, 178 bugs. Models: GPT-4o, GPT-4 Turbo, Claude 3 Opus/Sonnet/Haiku, GPT-4o-mini.
   - Repo: github.com/cla7aye15I4nd/patchagent-artifact (no licence), `patchagent-artifact-main.tar.gz` 56 MB. It holds the **full agent transcripts and patches per task per model** (`archives/<model>/<task>.json`, up to 15 attempts each).
   - My TSV: `patchagent/per_task_per_model.tsv`. Totals: Opus 151, Sonnet 108 and GPT-4 Turbo 126 match the paper; GPT-4o 137 vs 139 (two task files missing); Haiku 126 vs 128.
   - **No CVE IDs.** Tasks are named project-commit-bugtype, with fix commits listed. Only the 28 ExtractFix cases map to CVEs through paper Table 2. The OSS-Fuzz and Huntr bugs would need a commit-to-CVE join through OSV or NVD.
   - The paper also points to OSF https://osf.io/8k2ac, which lists a single `patchagent.zip` of 48 MB. Not opened.

9. **"Why LLMs Fail"** (arXiv 2603.10072). Vul4J, 64 CVEs, **one model only** (Gemini 3 Flash; the paper text also says 2.0 Flash once), 5 samples each.
   - `per_vuln_gemini3flash.tsv`, built from `results/evaluations/evaluation_summary.json`. The category totals (79 correct of 319) match.
   - Repo has no LICENSE file and no patches.

10. **CodeRover-S** (arXiv 2411.03346). 588 ARVO/OSS-Fuzz bugs, GPT-4o only, compared against Agentless and VulMaster.
    - github.com/nus-apr/code-rover-s-artifacts (no licence), 2.8 MB, downloaded. It holds the generated patches for all three tools and the bug reports, but **no per-instance pass/fail file**: you would have to re-run ARVO. Bugs are OSS-Fuzz IDs with essentially no CVEs.

11. **VRpilot** (arXiv 2405.15690). ChatGPT only. Per-case tables cover 10 ExtractFix C cases; the Java per-vulnerability detail is in a replication package (http://tinyurl.com/vrpilot-artifacts → Google Drive folder 1yrYUJS1r2cu7G6D3ezASsfugrNqgwc3v). **Not opened or verified.**

**C. Dead ends (aggregate results only, no per-task data found)**

- **WilliamT** (2505.13103): syzbot kernel bugs, no CVEs, no artifact. DeepSeek V3 and R1 **[DS]** appear only in an aggregate figure.
- **LiL / LiLCVE** (2605.28893): 116 Huntr CVEs. GPT-4o, GPT-5.2-Codex, DeepSeek-V4-Pro **[DS]** and MiniMax-M2.5 reported only as aggregates; no artifact.
- **VulnResolver** (2601.13933): SEC-bench, DeepSeek-V3.2-Exp **[DS]**; per-repository aggregates only, no artifact.
- **MemRepair** (2605.17444): DeepSeek v3.2/v3 **[DS]**, aggregates only. Its figshare link https://figshare.com/s/f2bbe7f7c8a759339368 returned 403. **Unverified.**
- **EvoRepair** (2605.30105): Zenodo 21093912, CC-BY-4.0, 36 MB, downloaded. It is code only; the scripts that export the repair matrix are there but their outputs are not. DeepSeek-v3.1 **[DS]**.
- **CVE-Bench repair** (NAACL 2025, Wang/Liu/Xiao): figures only, no artifact found.
- **REEF multilingual** (2508.03470): exact-match metrics only, no predictions released. The replication package (github salted-yu/AVRStudy and Zenodo 14542701) holds inputs and model checkpoints (multi-GB, not downloaded). DeepSeek-Coder 6.7B **[DS]**.
- **Antal et al.** (2506.11561): GPT-4o on Vul4J. Zenodo 15036667 (downloaded) has prompts and inputs only.
- **Camporese & Massacci** (2507.20977): a registered report with no results yet.
- **VulnLLMEval** (2409.10756) and **SoK AVR / Vul4C** (2501.18820): aggregates only; the Vul4C artifact was not checked.
- **Not checked further** (no open full text or artifact found): Ságodi et al. (EASE 2024, GPT-4 on Vul4J) and Zhang et al. (IWSPA 2024, 223 C/C++ snippets).

### Things to watch when joining
- **Vul4J overlap:** Wu, Garg, CWEFT, "Why LLMs Fail" and Antal all use Vul4J, so their CVE sets overlap heavily. Join on the CVE ID, not the VUL4J number.
- **ExtractFix/VulnLoc overlap:** SAN2PATCH, PatchAgent and Pearce share these CVEs.
- **Different success definitions:** PoC-only (VulnRepairEval), PoC plus tests (CWEFT L3, SAN2PATCH, Pearce), and manually judged correct (Wu, APPATCH).
- **Script hygiene:** helper scripts are in the session scratchpad, not in the data folders.

Files in the `studies/` folder are as listed above; the large archives are `appatch.zip` (164 MB), the PatchAgent and llm-vul tarballs (56 MB and 49 MB), the EvoRepair zip (36 MB) and Pearce's `final_results.csv` (29 MB).
