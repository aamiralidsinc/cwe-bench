# CWE-bench taxonomy

_Compiled 2026-10-15 from the CWE-bench paper (Collinear AI, arXiv 2610.17020 v1, Appendix E,
Table 5; Sections 3.2, 4.5, 5) and the project site cwe-bench.com._

## Summary

CWE-bench groups its vulnerabilities by the **OWASP Top 10 (2025 edition)**, in two levels:
**10 categories → 73 CWEs → 120 tasks**. It does not use MITRE's own CWE hierarchy or any CWE
"view" (such as CWE-1000 or CWE-699).

## What it is

A way to group the benchmark's vulnerabilities. Every task's weakness is a CWE ID, and every
CWE is filed under exactly one OWASP 2025 category. The paper uses it for two things:

- **Coverage.** The paper claims to cover "all ten OWASP Top 10:2025 categories"; other
  benchmarks reach 1 to 9 of the 10 (Table 1).
- **Reporting.** Results are given per category, not as one number (Section 4.5, Figure 5).

## Size

| Level | Count |
|---|---|
| Top-level categories | **10** (A01–A10) |
| Sub-categories | **none**: no middle level |
| CWEs (the leaves) | **73**, out of the 900+ in MITRE's catalogue (Section 5) |
| Total nodes | **83** (10 + 73), or 84 with a root. This is our count; the paper gives no node total. |
| Tasks | **120**, 10–14 per category, one target weakness per task (site) |

The training corpus is broader than the evaluation set: 4,000+ tasks over 215 distinct CWEs,
averaging about 3.3 weaknesses per task (site).

## Categories and their CWEs (Table 5)

| Category | Tasks | CWEs | Count* |
|---|---|---|---|
| A01 Broken Access Control | 13 | 22, 285, 441, 497, 601, 639, 862, 863, 918 | 9 |
| A02 Security Misconfiguration | 11 | 16, 310, 489, 611, 614, 776, 942, 1004 | 8 |
| A03 Software Supply Chain Failures | 10 | 1104, 1329, 1357, 1395 | 4 |
| A04 Cryptographic Failures | 13 | 208, 319, 326, 327, 330, 338, 347, 916 | 8 |
| A05 Injection | 14 | 20, 79, 89, 93, 94, 116, 470, 1336 | 8 |
| A06 Insecure Design | 12 | 73, 269, 362, 434, 444, 522, 693, 770, 913, 1284 | 10 |
| A07 Authentication Failures | 13 | 287, 288, 290, 295, 297, 306, 307, 613 | 8 |
| A08 Software or Data Integrity Failures | 11 | 345, 354, 494, 502, 565, 829, 915, 1321 | 8 |
| A09 Security Logging and Alerting Failures | 10 | 117, 532 | 2 |
| A10 Mishandling of Exceptional Conditions | 13 | 209, 252, 369, 390, 476, 674, 703, 755 | 8 |
| **Total** | **120** | | **73** |

\* Our tally. Table 5 lists the IDs but has no count column. The counts add up to 73, and no
CWE appears under two categories.

## What the paper found by category

- **Category matters more than language** for difficulty (abstract and Section 4.5).
- **A08 (integrity failures) is the hardest:** the best agent reaches only 57% pass@1.
- **A04 (cryptographic failures) is the easiest:** Claude Opus 5.5 reaches 90%.
- No single agent leads in every category (Section 4.5).
- The paper asks future benchmarks to report results per vulnerability class rather than as
  one number (Section 5).

## Where our 19 tasks fall

Mapped from the CWE IDs in each task's `task.toml`, using Table 5. A task can touch several
categories (stacked tasks especially).

| Task | Our CWEs | OWASP categories (per Table 5) | Not in Table 5 |
|---|---|---|---|
| actualbudget | 22, 284, 285, 306, 613, 862, 863 | A01, A07 | 284 |
| argo-workflows | 200, 522, 770, 862, 863 | A01, A06 | 200 |
| async-http-client | 287 | A07 | |
| asyncssh | 22, 287, 345, 354, 639, 835 | A01, A07, A08 | 835 |
| cloudreve | 22, 200, 359, 400, 770, 863 | A01, A06 | 200, 359, 400 |
| filament | 204, 294, 306, 862 | A01, A07 | 204, 294 |
| hickory-dns | 347 | A04 | |
| jackson-databind | 863 | A01 | |
| jackson-databind-sib | 863 | A01 | |
| jackson-sib7 | 863 | A01 | |
| py-shiny | 22 | A01 | |
| rclone | 287 | A07 | |
| rclone-sib | 287 | A07 | |
| ruby-saml | 287, 347, 400, 770 | A04, A06, A07 | 400 |
| russh | 129 | — | 129 |
| russh-sib | 129 | — | 129 |
| stigmem | 285, 319, 489, 494, 732, 770, 862, 863 | A01, A02, A04, A06, A08 | 732 |
| trigger-dev | 306, 639, 862, 918 | A01, A07 | |
| webob | 601 | A01 | |

**Tasks touching each category:**
- **Heavily covered:** A01 access control in 13 tasks, A07 authentication in 8.
- **Lightly covered:** A06 in 4, A04 in 3, A08 in 2 (only inside the stacked tasks asyncssh
  and stigmem), A02 in 1.
- **Not covered:** A03 supply chain, **A05 injection**, A09 logging, A10 exceptional conditions.

So relative to CWE-bench our set is skewed toward access control and authentication, and
A08, their hardest category, is barely represented.

## Notes on the sources

- **Stated vs counted:** the 10 categories, 73 CWEs, 120 tasks, 10–14 tasks per category and
  the A08/A04 results are stated in the paper. The node total and the per-category CWE counts
  are our own counts from Table 5.
- **Not in the paper:** "one target weakness per task" and the training-corpus figures come
  from cwe-bench.com, not the paper.
- **Images only:** the paper's per-category heatmap (Figure 5) and the site's per-CWE task
  counts are images, so exact per-CWE task numbers are not available.
