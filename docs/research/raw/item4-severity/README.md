# Item 4 raw material: CVSS / EPSS / KEV vs repair success

Findings: [../../severity_findings.md](../../severity_findings.md). Bulk downloads (benchmark
results, study artifacts, NVD feeds and records, EPSS, KEV; about 690 MB) are in
`~/.tb-graders/cwe/research-raw/item4-severity/`, indexed by its `INDEX.md`.

**Agent reports** (verbatim, saved 2026-10-16):
- `01-literature-cvss-epss-kev-vs-repair.md`: no published relation
- `02-inventory-benchmark-suites.md`: 14 repair benchmarks; public/private status, per-task results, transcripts
- `03-inventory-academic-studies.md`: about 25 studies

**Pipeline** (rerun in this order):
1. `build_outcomes.py`: reads the 13 sources and writes `outcomes_long.tsv` and `outcome_cves.txt`.
2. `seed_nvd_cache.py all_cves.txt`: fills the NVD cache from the bulk yearly feeds, with no API
   rate limit.
3. `fetch_severity.py all_cves.txt severity.tsv`: adds EPSS and KEV and writes the severity table.
   NVD is fetched from the API only for CVEs not already in the cache.
4. `analyse_outcomes.py [--runs-filter deepseek] [--drop BENCH]` writes
   `outcomes_analysis_output.txt` and `cvss_leave_one_out.txt`.

**Earlier, smaller analysis (superseded):** `analyse_severity.py` and `analysis_output.txt` cover
SEC-bench plus VulnRepairEval Table 6 only. Its inputs are `secbench_severity_joined.tsv`,
`vulnrepaireval_table6.tsv`, `secbench_cves.txt` and `vre_cves.txt`.

**Other files:**
- `our_task_cves.txt`: CVEs of our trialled tasks, kept to revisit later.
- `all_cves.txt`: every CVE fetched.
- `fetch*.log`: fetch logs. fetch3 and fetch4 were stopped and replaced by the bulk feeds;
  fetch5 is the final run.
