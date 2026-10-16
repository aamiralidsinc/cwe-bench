# Item 5 raw material: CAPEC / ATT&CK / STRIDE vs repair success

Findings: [../../attack_taxonomies_findings.md](../../attack_taxonomies_findings.md). Bulk downloads
are in `~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/`, indexed by its `INDEX.md`:
- `mitre/`: CAPEC 3.9 XML and ATT&CK Enterprise STIX
- `lit/`: papers, mappings and CVE → ATT&CK datasets

**Agent report:** `01-literature-and-mappings.md` (saved 2026-10-16): no published evidence;
lists the available mappings and their licences.

**Pipeline:**
1. `label_cves.py` reads `../item4-severity/all_cves.txt`, the NVD cache, CWE 4.20, CAPEC and
   ATT&CK, and writes `cve_attack_labels.tsv`.
2. `analyse_labels.py [--runs-filter deepseek] [--within-owasp] [--within-screener]` joins those
   labels with `../item4-severity/outcomes_long.tsv`. All five variants are saved, with a
   timestamp, in `analysis_output.txt`.
