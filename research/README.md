# Taxonomy research

The plan and tracker live in [../taxonomy_research.md](../taxonomy_research.md). Every research item
keeps **three things**:

| # | What | Where |
|---|---|---|
| 1 | **Findings**: what we learned, with numbers and sources | `<item>_findings.md` in this folder |
| 2 | **Screener change**, if the evidence supports one | `../sourcer/weights.json` (and code only if a new signal is needed) |
| 3 | **Raw material**: agent reports, source data, scripts | small text, data and scripts in this repo under `raw/<item>/` and `sources/`; bulk downloads (papers, PDFs, datasets, repo clones) outside the repo in `~/.tb-graders/cwe/research-raw/<item>/`, indexed by its `INDEX.md` |

Bulk material stays outside the repo because it is large and can be downloaded again.

| Item | Findings | Raw in repo | Bulk outside repo |
|---|---|---|---|
| 1 OWASP Top 10:2025 (+ per-CWE repair evidence) | [owasp_top10_findings.md](owasp_top10_findings.md) | `raw/item1-owasp-and-repair/` (8 agent reports), `sources/cwe-bench-site/`, `owasp2025_cwe_map.json`, `cwe_bench_v1_*.tsv`, `extract_cwe_bench.py` | `~/.tb-graders/cwe/research-raw/item1-owasp-and-repair/` (84 MB) |
| 2 MITRE CWE + CWE Top 25 | [cwe_hierarchy_top25_findings.md](cwe_hierarchy_top25_findings.md) | `sources/mitre/` (catalogue zip, Top 25 page), `cwe_hierarchy.tsv`, `cwe_top25_2025.tsv`, `extract_cwe_hierarchy.py` | `~/.tb-graders/cwe/research-raw/item2-cwe-top25/` (unzipped catalogue) |
| 4 CVSS / EPSS / CISA KEV | [severity_findings.md](severity_findings.md) | `raw/item4-severity/` (3 agent reports, pipeline scripts, outcomes and severity tables, outputs) | `~/.tb-graders/cwe/research-raw/item4-severity/` (690 MB: benchmark results, study artifacts, NVD feeds) |
| 5 CAPEC / ATT&CK / STRIDE | [attack_taxonomies_findings.md](attack_taxonomies_findings.md) | `raw/item5-attack-taxonomies/` (agent report, labelling and analysis scripts, CVE labels, outputs), `cwe_attack_classes.tsv` (read by the screener) | `~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/` (MITRE catalogues, literature downloads, mappings) |
