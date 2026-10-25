<!-- Verbatim final report of a research sub-agent (id a1b46f866f38f969a), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

STATUS: NOT COMPLETE. No per-CWE findings to report yet. I was told to hand back before any of my research results arrived, so this report has no new public numbers in it. I have not guessed or filled in any figures.

What I did:
- I checked the local workspace first. /Users/dev/terminal-bench/cwe-bench/taxonomy_research.md is a plan only: item 2a, "public per-CWE LLM data", is marked "not started", and it holds no per-CWE numbers. The memory note cwe-bench-failure-patterns.md (2026-10-14) gives failure patterns but no per-CWE tables.
- I started five parallel web researchers, all still running when I had to hand back:
  1. SEC-bench, PatchBench (arXiv 2609.04075), Beyond Resolution Rates (arXiv 2604.02547).
  2. LiL vulnerabilities (2605.28893), Vul4Py (2608.00692), the ESEM 2026 study (2608.18280), Vul4J/VJBench repair studies.
  3. AutoPatchBench/CyberSecEval 4, ARVO-based repair, VulnRepairEval, CVE-Bench, and the Collinear CWE-bench per-OWASP heatmap.
  4. Generation benchmarks, labelled as generation: SecRepoBench, BaxBench, CWEval, SecCodePLT.
  5. Other per-CWE repair studies: PatchEval, SecureAgentBench, APPATCH, SAN2PATCH, Pearce et al. S&P 2023, VRpilot, NAVRepair, plus any DeepSeek or MiMo repair results.
  Each was asked for: task type, language, task count, models (DeepSeek/MiMo flagged), per-CWE tables with n, quoted hardest/easiest findings, difficulty factors, and exact URLs. They were also told to write "no per-CWE data" instead of guessing.

Already known from earlier local notes (not checked again in this run, and not per-CWE):
- PatchBench: about 97% PoC pass vs about 59% truly solved.
- Collinear CWE-bench v1: DeepSeek-V4.1-Flash scores 55% pass@1 and 74% pass@4. It reports A04 Cryptographic Failures as its easiest category (Claude Opus 5.5 at 90%); I have no other per-category numbers. The per-category heatmap (Figure 5) is an image, and its numbers are not yet extracted.
- No MiMo repair results had been found anywhere as of 2026-10-14.
- ESEM 2026 (2608.18280, one agent only): many hunks, large gaps between hunks, many deleted lines and a wide repo structure predict difficulty.

Next step for the caller: wait for or re-run the five researchers (results are not available to me after this handback), or re-launch this task with permission to wait for background results before handing back. The cross-source summary (consistently hard CWEs, consistently easy CWEs, disagreements) cannot be written until those results exist.
