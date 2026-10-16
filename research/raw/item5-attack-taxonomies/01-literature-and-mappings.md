<!-- Final report of a research sub-agent (id ad775ae1f6413e3a7), saved 2026-10-16 from the session. Model output: verify against cited sources. Downloads are in ~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/lit/ -->

## Bottom line

**No.** No published paper, benchmark report or leaderboard reports LLM or agent vulnerability
*repair* success broken down by any of these:
- CAPEC attack pattern, mechanism of attack or domain of attack
- ATT&CK tactic or technique
- STRIDE class
- CWE Common_Consequences scope or technical impact
- CVSS sub-metrics: C/I/A impact, attack vector (AV), privileges required (PR)

The evidence for this is negative and moderately strong:
- About 25 web searches (standard and extended) found nothing.
- About 30 repair and benchmark papers were downloaded and their full text grepped for CAPEC,
  ATT&CK, STRIDE, confidentiality, attack vector, privileges required and technical impact. There
  were zero substantive hits in any repair paper: SEC-bench, PatchEval, CyberGym, BountyBench,
  SecRepoBench, VulnRepairEval, APPATCH, LiL, CVE-Factory/LiveCVEBench, CWE-bench (2610.17020),
  PatchBench, AgenticRepair, EvoRepair, VulKey, Vul4Py, "Why LLMs Fail", 2511.23408, the SoK on
  automated vulnerability repair, and others.
- Full text was not obtained for SAN2PATCH or AutoPatchBench. Their public summaries report
  results by bug or crash type only.

ATT&CK, attack-type and STRIDE breakdowns exist only for **exploitation, offense and threat
classification**. None of them is repair.

## Hits (none are repair)

1. **CVE-Bench (UIUC, Zhu et al.), arXiv 2503.17332, ICML 2025.** **Exploitation.**
   - It uses 8 "standard attack" types that work like impact classes: DoS, file access, file
     creation, database modification, database access, unauthorised admin login, privilege
     escalation, outbound service.
   - Fig. 2 shows how the attack types are distributed; Fig. 4 shows how successful exploits are
     distributed across them. Fig. 4 is a share of successes, not a success rate per type.
   - The only number in the text: among T-Agent's successful exploits, 68% (zero-day) and 30%
     (one-day) were database access; AutoGPT had 0%.
   - Model: gpt-4o-2024-11-20 on 40 CVEs. Repo: https://github.com/uiuc-kang-lab/cve-bench.
     Per-task results not checked.
2. **LLM-CVX (El Yagouby et al.), ACM AISec 2025** (DOI 10.1145/3733799.3762978). **Exploitation.**
   - 14 LLMs, 36 CVEs, each mapped to ATT&CK tactics and techniques by hand.
   - The paper analyses results per tactic and technique, but the numbers were **not seen**: the
     full text was blocked (403), and only search snippets were read.
3. **3CB (Apart Research), arXiv 2410.09114.** **Offense.**
   - 15 challenges, one per ATT&CK tactic, so each tactic is a single challenge.
   - Fig. 4 gives completion rate per model per challenge; runs are public.
4. **CyberSecEval 1 (Meta), arXiv 2312.04724.** **Willingness to help attackers.**
   - 1,000 prompts, 100 per ATT&CK category; average compliance across models was 52%.
   - Models refused most on evasion and execution and complied most on discovery and recon.
5. **SeCodePLT, arXiv 2410.11096.** **Offense.**
   - Attack categories based on ATT&CK; end-to-end attack success was 0 for GPT-4o, Claude 3.5
     Sonnet and Llama-3.1-70B.
6. **"LLMs' suitability for network security: STRIDE" (AbdulGhaffar & Matrawy), arXiv 2505.04101.**
   **Threat classification.**
   - 5 LLMs classify six 5G threats into STRIDE; models missed Repudiation on a man-in-the-middle
     threat.
7. **Adjacent:**
   - **BountyBench** grades patches with confidentiality, integrity and availability invariants
     but never breaks results down by them.
   - **1Password / Off-by-1 Labs, F.L.A.W.E.D. (2026):** 6 CVEs, results per CVE only; a fully
     clean fix 26.0% of the time.
8. **CWE-family groupings:** CVE-Factory / LiveCVEBench App. C.1 and Table 6 (already covered in
   item 1). Success by family: code injection 10.8%, path traversal 17.9%, access control 27.1%,
   XSS 25.1%, injection 38–47%, OS command injection 46.6%.

## Mappings

**(a) CWE → STRIDE.** There is no official mapping from MITRE, Microsoft or OWASP.
- **Honkaranta, Leppänen & Costin, FRUCT29 (2021), https://old.fruct.org/publications/fruct29/files/Hon.pdf**
  - Table III maps the 2020 CWE Top 25 to STRIDE.
  - **Table IV gives a rule from technical impact to STRIDE:** Modify → T; Read → I; DoS → D;
    Execute unauthorised code → E; Bypass protection → E; Gain privileges / assume identity → S;
    Hide activities → R.
  - Applied to CWE 4.20, it gives 302 CWEs no letter, 289 one letter and 353 two or more.
  - Top-25 CWEs mostly get 3–5 letters, so the label separates CWEs poorly.
  - Licence not stated.
- **Threagile (MIT):** 42 risk rules, each with one CWE and one STRIDE value; about 25 CWEs.
- **Checked, but no CWE → STRIDE inside:**
  - Microsoft TMT template (STRIDE labels, no CWE)
  - OWASP pytm threats.json (CAPEC and CWE, no STRIDE)
  - OWASP Threat Dragon (category names only)
  - IriusRisk (commercial; unverified)
  - NyxFoundation (labels assigned by an LLM, no licence)

**(b) CAPEC → STRIDE.**
- **OWASP Cornucopia webapp-mappings-3.0.yaml (CC-BY-SA-4.0):** 80 cards with STRIDE letters and
  CAPEC IDs; 197 CAPECs, 87 of them with more than one letter. This is a card-level association,
  not a curated classification.
- **Crawley's mind maps:** images only, no licence.
- **STRIDE ↔ ATT&CK (Rebultan):** no licence; the STRIDE encoding in the xlsx is unverified.

**(c) CAPEC → ATT&CK and CVE → ATT&CK.**
- **Official CAPEC 3.9 → ATT&CK:**
  - 272 mappings, covering 177 of 615 CAPECs and 189 techniques. Licence: MITRE terms of use.
  - **Only 336 of 969 CWEs link to any CAPEC.** CWE-787, 416, 476 and 863 link to none.
  - The CAPEC "Mechanisms of Attack" view is nearly single-label: 543 of 558 live patterns get
    exactly one class.
- **CTID "Mapping ATT&CK to CVE for Impact" (Apache-2.0):** 839 CVEs from 2008–2020.
  https://github.com/center-for-threat-informed-defense/attack_to_cve
- **CTID Mappings Explorer, KEV → ATT&CK 16.1 (Apache-2.0):** 419 CVEs.
- **CIRCL gold set (CC-BY-4.0), arXiv 2607.25572:** 1,207 CVEs, the union of the two CTID sets.
  - **Caveat:** the CWE → CAPEC → ATT&CK chain (CVE2CAPEC, BRON) is very noisy. On 2024 CVEs it
    assigns a median of 8 techniques per CVE, and T1574.007 lands on 53% of them as an artefact
    of how the tables expand.
- **Others:** BRON (MIT), SMET (MIT), CVE2ATT&CK (no licence), VTT-LLM, TRIAGE. None covers repair.

## Could not verify
- LLM-CVX per-tactic numbers.
- Per-task results in CVE-Bench and exact values in its Fig. 4.
- SAN2PATCH and AutoPatchBench full text.
- How STRIDE is encoded in Rebultan's xlsx.
- Whether IriusRisk's library is accessible.
- The licence on Hon's tables.
- Whether CAPEC 3.9's ATT&CK IDs are current in ATT&CK 16.

## Files (~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/lit/)
- **official/:** CAPEC 3.9, CWE 4.20, CSV exports
- **derived/:**
  - capec_to_attack, capec_to_cwe, capec_mechanisms_domains, cwe_common_consequences
  - cwe_to_stride_via_hon_tableIV, cwe_to_capec_mechanism_attack
  - threagile_rule_cwe_stride, cornucopia_v3_card_capec_stride
- **ctid/:** attack_to_cve CSV, methodology and licence; KEV → ATT&CK 16.1 JSON
- **cve2attack-datasets/:** CIRCL parquet files, SMET, CVE2ATT&CK
- **threat-modelling-tools/:** Cornucopia, pytm, Rebultan
- **papers/:** 2503.17332, 2410.09114, 2312.04724, 2410.11096, 2602.03012, 2505.04101,
  2505.15216, 2512.18751, Hon FRUCT29, CIRCL 2607.25572, F.L.A.W.E.D.
