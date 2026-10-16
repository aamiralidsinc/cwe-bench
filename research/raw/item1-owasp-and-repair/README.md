# Item 1 raw material (OWASP Top 10:2025 and per-CWE repair evidence)

**What these files are:**
- Verbatim final reports of the research sub-agents run on 2026-10-16. They are model output:
  check any number against the source it cites before relying on it.
- The findings built from them: [../../owasp_top10_findings.md](../../owasp_top10_findings.md).
- The downloaded papers, pages and datasets they used are in
  `~/.tb-graders/cwe/research-raw/item1-owasp-and-repair/` (see its `INDEX.md`).

| File | Covers |
|---|---|
| 00-first-attempt-returned-early.md | first repair-research attempt; returned before its workers finished (no data) |
| 01-cwe-bench-per-category-and-per-cwe.md | CWE-bench v1/v0 per OWASP category and per CWE, per model (incl. DeepSeek V4.1 Flash) |
| 02-owasp-2025-cwe-mapping.md | official OWASP Top 10:2025 CWE lists, errata, MITRE view CWE-1450 |
| 03-secure-generation-benchmarks.md | BaxBench, SecRepoBench, CWEval, SecCodePLT, CyberSecEval (generation, not repair) |
| 04-repair-autopatchbench-arvo-vulnrepaireval-cvebench.md | AutoPatchBench, CodeRover-S, PatchBench, WilliamT, CyberGym-E2E, VulnRepairEval, CVE-Bench variants |
| 05-repair-other-per-cwe-studies.md | multilingual repair (REEF), LiveCVEBench, PatchAgent, SAN2PATCH, Java/Vul4J, VSP, PatchEval factors |
| 06-repair-lil-vul4py-esem-vul4j.md | LLM-in-the-loop (LiL), Vul4Py, CWEFT (ESEM 2026), Vul4J studies, Garg et al. injected variants |
| 07-repair-secbench-patchbench-beyondresolution.md | SEC-bench per crash class (computed from its per-run results), PatchBench, Beyond Resolution Rates |
