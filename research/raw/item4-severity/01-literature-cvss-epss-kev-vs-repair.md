<!-- Verbatim final report of a research sub-agent (id a3ba93edcc3e74b98), saved 2026-10-16 from the session transcript. Model output: verify against cited sources. -->

## Report: vulnerability severity and exploitation signals vs. LLM repair success (searched 2026-10-16, all by direct web search and fetch, no sub-agents)

**Bottom line:** I found no published study that reports LLM or agent repair success as a function of CVSS, EPSS or CISA KEV. The only repair paper that puts CVSS into a model of repair success is LiL (arXiv 2605.28893). It uses CVSS as a control variable and does not report a coefficient for CVSS itself. Every other repair benchmark I opened either never mentions severity or reports it only as a description of its dataset.

### A. Repair papers: what each one does with severity

1. **LiL, "Towards Demystifying and Repairing LLM-in-the-Loop Vulnerabilities"** (Ma et al.), https://arxiv.org/html/2605.28893v2. Repair.
   - **The regression (§IV-B2):** logit(Pr(Y_ij=1)) = α + βS_i + γ_j (Agent–LLM fixed effects) + δᵀX_i. S_i flags an LLM-in-the-loop (LiL) vulnerability. X_i are the CVE-level controls: "programming language, severity and disclosure year".
   - **Table IV** gives only the odds ratio for the LiL flag S:

     | Model | Control | OR (95% CI) | p |
     |---|---|---|---|
     | M1 | none | 0.578 (0.350–0.957) | 0.033 |
     | M2 | agent | 0.567 (0.325–0.987) | 0.045 |
     | M3 | language | 0.586 (0.349–0.983) | 0.043 |
     | M4 | CVSS | 0.557 (0.335–0.927) | 0.024 |
     | M5 | year | 0.595 (0.359–0.986) | 0.044 |

     The text adds that "the largest OR is 0.776 (combining all factors we considered)". That combined model is not in the table.
   - **What is missing:**
     - No β or OR is reported for CVSS itself.
     - It is not stated whether CVSS enters as a score or as a band.
     - The number of observations is not stated.
     - There is no Pass@1 breakdown by severity.
   - **What it does tell us:** adding a CVSS control barely moves the LiL effect (0.578 → 0.557). The authors' only claim is that low LiL repair "is not explained by differences in … severity". Separately, LiL vulnerabilities are more severe (51.2% Critical) and harder to repair: an average Pass@1 of 25.8%, which the paper says is 10.8 and 15.5 points below the other groups. The 15.5 comparison uses the "Traditional Bench" column of Table III, which is taken from published leaderboards, not the same experiment.
   - **Data:** 41 LiL and 75 LLM-ecosystem CVEs, 20 configurations. The models are GPT-4o, GPT-5.2-Codex, **DeepSeek-V4-Pro** and MiniMax-M2.5, each run under OpenHands, SWE-agent, Aider, AutoCodeRover and Agentless. No MiMo.
   - **Internal inconsistencies:**
     - The abstract says "15.5%/30.3% more critical"; §II-C says 28.8%/35.1%.
     - The text and Table III disagree on the direction of the OpenHands + DeepSeek-V4-Pro numbers (60.00 vs 41.46).
   - **Verdict:** CVSS is a control only. This is not evidence about severity and repair.

2. **VulnRepairEval**, arXiv 2509.03331, https://arxiv.org/html/2509.03331. Repair.
   - CVSS, EPSS, KEV and "severity" do not appear.
   - The only difficulty breakdown is an expert Easy/Medium/Hard tier based on "technical complexity required for discovery and exploitation", not severity. Table 4 counts successes per tier, but the per-tier denominators are not given.
   - 23 CVEs. Includes **DeepSeek R1 671B** (the only model that fixed a Hard case, 1) and DeepSeek V3.
   - No severity evidence.

3. **PatchEval**, arXiv 2511.11019, https://arxiv.org/html/2511.11019. Repair.
   - CVSS, EPSS, KEV and severity do not appear in the full text.
   - Breakdowns are by language (Table 3) and patch complexity (Table 9 / RQ5).
   - 1,000 CVEs, of which 230 are run dynamically; the best result is 23.0% (53/230). Includes DeepSeek-R1 and DeepSeek-V3.
   - No severity evidence.

4. **SEC-bench**, arXiv 2506.11791, https://arxiv.org/html/2506.11791. Repair and PoC.
   - CVSS appears only as a dataset histogram (Appendix A, Fig. 3): "a significant concentration … in the high and critical ranges (7.0-10.0)".
   - Severity is never related to success. This is a descriptive mention only.
   - Results: 200 instances, 34.0% patch and 18.0% PoC success. Models were Claude 3.7 Sonnet, GPT-4o, o3-mini and Claude 3 Haiku; no DeepSeek.
   - It also contains a recency test, reported under section C.

5. **CVE-Factory / LiveCVEBench**, arXiv 2602.03012, https://arxiv.org/html/2602.03012.
   - CVSS and KEV are used only to pick which CVEs to build tasks from:
     - Eq. (1): S_final = … + (CVSS×2) + …
     - Table 5 "Reproduce Score": "CISA KEV / SSVC" earns +20–25 and "PoC / Exploit URL" earns +30.
   - No success rate is broken down by CVSS or KEV. Breakdowns are by language/CWE, by date before vs. after model release, by container count, and by domain.
   - Table 8 covers 190 tasks and includes DeepSeek V3.2 and V3.1-Terminus.
   - No severity evidence.

6. **Vul4Py**, arXiv 2608.00692, https://arxiv.org/html/2608.00692. Repair.
   - CVSS, EPSS, KEV and severity do not appear; a PoC indicator is used only as a filter.
   - 100 instances; no DeepSeek or MiMo.
   - No severity evidence.

7. **CWE-bench**, arXiv 2610.17020, https://arxiv.org/html/2610.17020. Repair.
   - CVSS, EPSS, KEV and severity do not appear.
   - Breakdown by OWASP 2025 category over 120 tasks: A08 is hardest (best 57%), A04 easiest (Opus 5.5 at 90%).
   - **DeepSeek V4.1 Flash** scores 55% pass@1 and 74% pass@4. No MiMo.
   - No severity evidence.

8. **CVE-Bench, repair version** (Wang, Liu, Xiao; NAACL 2025), https://aclanthology.org/2025.naacl-long.212.pdf. Repair.
   - Appendix A, Fig. 9(b) and Fig. 10 show the dataset's CVSS and severity distribution only (509 CVEs).
   - No success rate by severity. Descriptive only.

9. **"On the Evaluation of LLMs in Multilingual Vulnerability Repair"**, arXiv 2508.03470 (Wang et al.). Repair.
   - CVSS v4.0 bands are used only to describe the 10,649-vulnerability dataset: "1.2% … low … 61.3% … high or critical".
   - Table 6 gives exact match per CWE for the Top-25 CWEs. Examples for GPT-4o: CWE-79 at 40.87% (n=252), CWE-125 at 0% (n=44).
   - There is no Top-25 vs. other comparison and no severity comparison. Includes DeepSeek-Coder.
   - Descriptive only.

10. **Other repair papers with no severity analysis:**
    - "Why LLMs Fail" (2603.10072): the predictors are CWE and human patch size (Spearman ρ = −0.331, p = 0.008), not severity.
    - "One-Shot Patching of Real and Artificial Vulnerabilities" (2511.23408): Table 1 lists CVSS per CVE (5.5–9.8) for 15 real CVEs, but no analysis. It includes DeepSeek R1 Qwen 32B.
    - ZeroDayBench (2603.02297): only CVSS ≥ 7.0 is included, so severity cannot vary.
    - Systematic patching architectures (2603.01257).
    - MemRepair (2605.17444, abstract only).
    - "Helpful or Harmful?" human study (2606.25973).

### B. Closely related signal: CVE age and memorisation (repair)

These all measure age or contamination, not severity.

- **CVE-Bench (NAACL 2025), §3.5, Fig. 7(a).** GPT-4 SWE-agent, white-box, on 50 Python CVEs published after November 2023 versus CVEs collected before then. "the repair rate on recent CVEs is lower than that of pre-collected CVEs." The numbers appear only in the figure, not the text.
- **SEC-bench, §3.2, Table 5.** 15 instances before and 15 after each model's cutoff, using SWE-agent:

  | Model, task | Before cutoff | After cutoff |
  |---|---|---|
  | GPT-4o, patch | 33.3% | 40.0% |
  | Claude 3 Haiku, patch | 20.0% | 13.3% |
  | GPT-4o, PoC | 6.7% | 0% |
  | Claude 3 Haiku, PoC | 0% | 0% |

  The Wilcoxon test gives p = 0.27, so there is no significant difference.
- **CVE-Factory, §4.2.3, Fig. 4.** "Nearly all models degrade on post-release CVEs" (the exception is Sonnet 4.5 on Terminus-2). The numbers are only in the figure. Section 5 attributes the drop to repository familiarity.

**Verdict on age:** mixed, with small samples.

### C. Not repair: detection and exploitation

- **Detection: Shu et al., arXiv 2506.07503, §3.3, Figs. 8–9.** Results are grouped by CVSS severity, but only to compare models within each band.
  - Function level, High: GPT-4o ITFSP 630 vs CodeT5P 514. Critical: 305 vs 321.
  - Line level, Critical: 134 vs 76.
  - There is no within-model comparison across severity bands, and the denominators are not given in the text.
  - Verdict: not evidence that severity changes how well a model performs.
- **Exploitation: Fang et al., "LLM Agents can Autonomously Exploit One-day Vulnerabilities"**, arXiv 2404.08144, Table 2.
  - CVSS is listed for each of 15 vulnerabilities, and GPT-4 succeeds on 87% of them.
  - Its two failures are Iris XSS (4.6) and Hertzbeat RCE (9.8). The authors explain them by app complexity and a Chinese-language description, not severity.
  - 82% (9/11) success on vulnerabilities after the cutoff.
  - No severity analysis.
- **Exploitation: CVE-Bench (Zhu et al.)**, arXiv 2503.17332. Only CVSS 3.1 ≥ 9.0 is included. There is no severity analysis. Models: gpt-4o and Llama 3.1.
- **Exploitation: CyberGym (2506.02548), CVE-Genie (2509.01835), web reproduction (2510.14700), VEX-Bench (2609.08040).** None relates CVSS, EPSS or KEV to success.
  - CVE-Genie reports only that having a PoC in the advisory "significantly" helps reproduction ("60% with PoC", 60 CVEs). It gives no rate without a PoC.
  - VEX-Bench evaluates DeepSeek-V4-Pro and V4-Flash.
- **EPSS has only been studied as a prediction target.** Empirical Security's benchmark finds that "LLMs underperform EPSS" at predicting 30-day exploitation (https://research.empiricalsecurity.com/research/benchmarking-llms). That is about forecasting exploitation, not repair.

### Verdict per signal

- **CVSS: not studied** as a predictor of LLM repair success. LiL uses it only as a control and reports no CVSS effect. Six or more benchmarks report it only as a dataset distribution or a selection filter, and those do not count as evidence. The one indirect hint is from LiL: its LiL group is both more critical and repaired less often, but that was not tested as an association between severity and success.
- **EPSS: not studied.** I found no repair, detection or exploitation benchmark that conditions results on EPSS.
- **KEV: not studied.** It appears only as a +20–25 term for selecting CVEs in CVE-Factory.
- **Closest proxies:**
  - CVE age and memorisation: weak or mixed (CVE-Bench and CVE-Factory show a drop on newer CVEs; SEC-bench finds none, p = 0.27).
  - PoC available: weak, and for reproduction only (CVE-Genie).
  - CWE type: strong variation (0–45% fix rates), but that is not severity.

**Model flags:**
- DeepSeek appears in LiL (V4-Pro), VulnRepairEval (R1, V3), PatchEval (R1, V3), CVE-Factory (V3.2, V3.1-Terminus), CWE-bench (V4.1 Flash), the multilingual repair paper (DeepSeek-Coder), one-shot patching (R1-Qwen-32B) and VEX-Bench (V4-Pro, V4-Flash).
- Xiaomi MiMo appears in none of the papers I read.

### Gaps in this search

- Numbers that exist only in figures were not readable: CVE-Bench Fig. 7, CVE-Factory Fig. 4, the CyberGym contamination table, and 2506.07503 Figs. 8–9.
- For the SoK on automated vulnerability repair (2501.18820) I read only the abstract.
- I did not do a full-text check of the second half of every long paper. PatchEval was fully checked.
