# Item 5: CAPEC, ATT&CK and STRIDE vs LLM repair success

Research date 2026-10-16. Tracker: [../taxonomy_research.md](../taxonomy_research.md) items 5a–5c.
Raw material: [raw/item5-attack-taxonomies/](raw/item5-attack-taxonomies/README.md); bulk downloads in
`~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/` (see its `INDEX.md`).

## Bottom line

- **Nobody has published this relation.** No repair paper or benchmark breaks results down by
  CAPEC, ATT&CK, STRIDE or impact type
  ([literature report](raw/item5-attack-taxonomies/01-literature-and-mappings.md), about 30 papers
  grepped). ATT&CK and STRIDE breakdowns exist only for *exploitation and offense*. So we inferred
  the relation ourselves, with the same 13-source outcome table and method as
  [item 4](severity_findings.md).
- **One group of labels holds up: attacks that steal credentials or gather information.** CVEs
  that map to the ATT&CK tactic *credential-access* or the CAPEC mechanism *Collect and Analyze
  Information* are fixed **8–19 points less often**. They pass the correction for many tests in
  most variants: all runs, inside each OWASP category, DeepSeek runs only, and among CVEs our
  screener already scores the same. The CWEs behind them are input validation (20), authorisation
  (862, 863, 284, 639), authentication (287, 522, 613) and information exposure (200).
- **But the agent benchmark closest to our setup shows nothing.** LiveCVEBench: +0.4 points on 76
  CVEs. The effect comes mostly from PatchEval (models prompted directly, without an agent) and
  the Java studies.
- **Everything else is noise:** STRIDE, CAPEC domains, CVSS attack vector, privileges, user
  interaction, CAPEC skill and likelihood.
- **Bonus: our screener passes an outside check.** CVEs our current `weights.json` favours (weakness
  points ≥ 2) are fixed 7.4 points less often across the 13 sources (p = 0.004). DeepSeek runs
  alone show no gap (−2.2, p = 0.61).
- **Screener change: label only, 0 points** (decided 2026-10-16, option a). Candidates whose CWE
  maps to either class carry `S5 Attack class: …` in their score detail; scores are unchanged.
  855 of 1,464 scored candidates get the label (723 credential-access), so in our web-heavy pool
  it is broad. Revisit with our own trial results.

## How the labels were made

| Label | Chain | CVEs labelled (of 922) | Notes |
|---|---|---|---|
| CAPEC mechanism (9 classes, view 1000) | CVE → CWE (NVD) → CAPEC (both directions of the official links; nearest CWE ancestor if none) → ancestors → class | 808 | Only 336 of 969 CWEs link to CAPEC; 200 CVEs labelled through an ancestor CWE |
| CAPEC domain (view 3000) | same | 808 | "Software" applies to every CVE, so it isn't testable |
| ATT&CK tactic | CAPEC → ATT&CK technique (official mapping) → tactic (ATT&CK Enterprise STIX) | 282 | **Noisy chain:** CIRCL (arXiv 2607.25572) shows it spreads techniques widely. Hand-made sets (CTID, CIRCL gold) cover only 3 of our CVEs, so they can't replace it |
| STRIDE | CWE Common_Consequences impacts → letters | 854 | Same rule as Honkaranta et al. FRUCT29 Table IV. Most CWEs get 3+ letters, so it separates poorly |
| CAPEC skill / likelihood | lowest skill and highest likelihood over the CVE's CAPECs | 691 / 769 | |
| CVSS AV / PR / UI / C / I / A | NVD vector | 904 | |

Every label is a function of the CVE's CWEs (except the CVSS ones). So the question is whether
grouping CWEs by *how they are attacked* finds hard ones that our OWASP and per-CWE weights miss.
The `--within-owasp` and `--within-screener` runs answer that directly.

## Results

**Method:** as in item 4. The unit is a CVE within a benchmark; groups are compared inside each
benchmark (or each benchmark × OWASP category, or benchmark × screener points); p comes from a
stratified permutation; q is Benjamini–Hochberg over all ~40 labels. Full output:
[analysis_output.txt](raw/item5-attack-taxonomies/analysis_output.txt).

### Labels that survive correction (q < 0.05) somewhere

Each cell gives the difference in points and q. Group sizes are in the output file.

| Label | All runs | Within OWASP category | Within screener points | DeepSeek only | DeepSeek, within screener |
|---|---|---|---|---|---|
| ATT&CK credential-access | **−15.4, q 0.04** | **−18.8, q 0.02** | −13.4, q 0.06 | **−17.4, q 0.02** | −20.6, q 0.06 |
| CAPEC Collect and Analyze Information | −7.8, q 0.65 | **−12.6, q 0.02** | **−10.3, q 0.05** | **−13.2, q 0.006** | −11.2, q 0.08 |
| CAPEC domain Communications | −2.1, q 0.87 | −9.7, q 0.05 | **−10.0, q 0.05** | **−12.5, q 0.006** | −13.8, q 0.06 |
| Has any ATT&CK mapping | −5.9, q 0.21 | −7.8, q 0.08 | −7.4, q 0.06 | **−11.9, q 0.006** | −10.3, q 0.08 |
| STRIDE Repudiation | +8.2, q 0.32 | **+16.6, q 0.02** | n.s. | n.s. | n.s. |

All of these labels say "harder", except Repudiation, which says "easier" and is unstable. They
overlap heavily: 115 of the 153 credential-access CVEs are also Collect and Analyze Information.

### Per benchmark (all runs)

**Credential-access** is lower in 8 of 11 benchmarks:

| Benchmark | Difference |
|---|---|
| "Why LLMs Fail" | −41.7 |
| PatchEval | −26.4 (78 vs 30 CVEs) |
| Wu | −23.9 |
| CWEFT | −20.6 |
| VulnRepairEval | −16.7 |
| Gatti | −15.7 |
| APPATCH | −8.5 |
| BountyBench | −6.2 |
| Garg | 0 |
| LiveCVEBench | +0.4 (24 vs 52 CVEs) |
| SEC-bench | +1.9 (1 CVE) |

**Collect and Analyze Information** is lower in 8 of 13.

The agent benchmarks closest to ours either show nothing (LiveCVEBench) or have almost no such
CVEs (SEC-bench is C/C++ memory bugs).

### Not related (no variant passes correction)

- **STRIDE** Spoofing, Tampering, Information disclosure, DoS and Elevation of privilege: all
  within ±9 points, p ≥ 0.15.
- **CAPEC mechanisms:** Inject Unexpected Items, Manipulate Data Structures, Subvert Access
  Control, Abuse Existing Functionality, Manipulate System Resources.
- **CAPEC** skill and likelihood.
- **CVSS:** AV network, PR none, UI none and A high are null. High C/I impact is *easier*
  (+5 points, p ≈ 0.02), the same direction as item 4's CVSS result.

## What this means for us

1. **Our screener already points the right way** on outside data. Item 1–2 weights separate
   harder CVEs from easier ones across 13 benchmarks, though not in DeepSeek runs alone.
2. **A credential/information-gathering bonus is plausible but not proven for agents.** It holds
   up statistically, adds to our existing weights, and holds for DeepSeek. But it is absent in
   LiveCVEBench, and it rests on a noisy CWE → CAPEC → ATT&CK chain. Its CWEs (20, 200, 284,
   287, 862, 863, 639, 522, 613) are mostly access-control and authentication logic. Those are
   the "wrong layer" and "fix the symptom" bugs our failure-pattern research already favours.
3. **STRIDE is useless for scoring.** Most CWEs get 3+ letters, and no class matters.
4. **Experiment design (from the plan, unchanged by the data):**
   - CAPEC patterns linked to a CWE can still serve as a checklist of exploit variants for
     sibling injection and security tests.
   - Stacking should mix mechanisms, e.g. one *Collect and Analyze Information* bug plus one
     *Inject Unexpected Items* bug.

**Screener options (decided 2026-10-16: (a)):**
- **(a) Label only, 0 points** (like the Top 25 label), revisit with our own trials. **Chosen.**
  Implemented as `weakness.attack_label` in `../sourcer/weights.json`. It reads
  [cwe_attack_classes.tsv](cwe_attack_classes.tsv), one row per CWE, written by
  `raw/item5-attack-taxonomies/label_cves.py`.
- **(b) +1 point** for a CVE whose CWE maps to ATT&CK credential-access or CAPEC Collect and
  Analyze Information. The data would come from a CWE → class table exported from
  `cve_attack_labels.tsv` logic.
- **(c) No change.**

## Limits

- Every label is derived from the CWE. NVD's CWE choice and the ancestor fallback (200 CVEs)
  add noise.
- Hand-made ATT&CK labels for our CVEs don't exist (overlap 3 of 922).
- Success rules differ by source, as in item 4.
- No MiMo data; DeepSeek data is older models (V3, R1, V3.1/V3.2, Coder-V2).
- About 40 labels were tested per variant across 5 variants. The table above shows only labels
  that pass correction in at least one variant, so read single q-values near 0.05 with care.
