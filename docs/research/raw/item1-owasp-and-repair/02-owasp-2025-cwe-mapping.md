<!-- Verbatim final report of a research sub-agent (id a65481eeaeb3af416), saved 2026-10-16 from the session transcript. Model output: verify numbers against the cited sources. -->

## OWASP Top 10:2025 → CWE mapping (official)

**Bottom line:** The full mapping exists and I parsed it from the official sources. There are **249 CWE entries across A01–A10, and no CWE appears in two categories**, so each listed CWE falls into exactly one category. Each category's list length matches the "CWEs Mapped" figure in its own score table. Two caveats matter for a screening script:
- **A03 lists CWE-447, which is a typo for CWE-477.** The name OWASP gives ("Use of Obsolete Function") is CWE-477's name; CWE-447 is "Unimplemented or Unsupported Feature in UI". This is reported in issue #838 (closed without being fixed), issue #907 (open) and open PRs #909/#910, but it is still unfixed upstream.
- **Many common CWEs are in no A01–A10 list** (memory safety, resource exhaustion, ReDoS, etc.). The script needs an "unmapped" result.

### Sources
- **Live pages:** `https://owasp.org/Top10/2025/<slug>/`, where slug is `A01_2025-Broken_Access_Control`, `A02_2025-Security_Misconfiguration`, `A03_2025-Software_Supply_Chain_Failures`, `A04_2025-Cryptographic_Failures`, `A05_2025-Injection`, `A06_2025-Insecure_Design`, `A07_2025-Authentication_Failures`, `A08_2025-Software_or_Data_Integrity_Failures`, `A09_2025-Security_Logging_and_Alerting_Failures` or `A10_2025-Mishandling_of_Exceptional_Conditions`. Each has a "List of Mapped CWEs" section; none is missing.
- **Repo source:** `https://github.com/OWASP/Top10/blob/master/2025/docs/en/<same slug>.md`. I used a clone of master at commit 3a31f353 (24 Sep 2026). The CWE IDs on the live pages and in the repo are identical for all ten categories (scripted comparison).

### 1 + 4. Mapping table (category | count | CWE IDs)
```
A01:2025 Broken Access Control | 40 | 22, 23, 36, 59, 61, 65, 200, 201, 219, 276, 281, 282, 283, 284, 285, 352, 359, 377, 379, 402, 424, 425, 441, 497, 538, 540, 548, 552, 566, 601, 615, 639, 668, 732, 749, 862, 863, 918, 922, 1275
A02:2025 Security Misconfiguration | 16 | 5, 11, 13, 15, 16, 260, 315, 489, 526, 547, 611, 614, 776, 942, 1004, 1174
A03:2025 Software Supply Chain Failures | 6 | 447 [sic, intended 477], 1035, 1104, 1329, 1357, 1395
A04:2025 Cryptographic Failures | 32 | 261, 296, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 334, 335, 336, 337, 338, 340, 342, 347, 523, 757, 759, 760, 780, 916, 1240, 1241
A05:2025 Injection | 37 | 20, 74, 76, 77, 78, 79, 80, 83, 86, 88, 89, 90, 91, 93, 94, 95, 96, 97, 98, 99, 103, 104, 112, 113, 114, 115, 116, 129, 159, 470, 493, 500, 564, 610, 643, 644, 917
A06:2025 Insecure Design | 39 | 73, 183, 256, 266, 269, 286, 311, 312, 313, 316, 362, 382, 419, 434, 436, 444, 451, 454, 472, 501, 522, 525, 539, 598, 602, 628, 642, 646, 653, 656, 657, 676, 693, 799, 807, 841, 1021, 1022, 1125
A07:2025 Authentication Failures | 36 | 258, 259, 287, 288, 289, 290, 291, 293, 294, 295, 297, 298, 299, 300, 302, 303, 304, 305, 306, 307, 308, 309, 346, 350, 384, 521, 613, 620, 640, 798, 940, 941, 1390, 1391, 1392, 1393
A08:2025 Software or Data Integrity Failures | 14 | 345, 353, 426, 427, 494, 502, 506, 509, 565, 784, 829, 830, 915, 926
A09:2025 Security Logging & Alerting Failures | 5 | 117, 221, 223, 532, 778
A10:2025 Mishandling of Exceptional Conditions | 24 | 209, 215, 234, 235, 248, 252, 274, 280, 369, 390, 391, 394, 396, 397, 460, 476, 478, 484, 550, 636, 703, 754, 755, 756
```

**Names:** A09's page heading uses "&"; the index page writes "Security Logging and Alerting Failures".

**JSON file:** `/private/tmp/claude-501/-Users-dev-terminal-bench/1fc8f0a5-f4cd-49c9-bf92-354befe55ca0/scratchpad/owasp2025_cwe_map.json` holds the IDs, stats and source URL per category. It lists 447 as OWASP publishes it. CWE names are in `.../scratchpad/owasp/map.json`.

**Other list problems** (I checked every entry against MITRE CWE 4.20):
- **Not weaknesses:** CWE-16 and CWE-320 are obsolete categories, and CWE-1035 is the OWASP 2017 A9 category.
- **Wrong names, plausible IDs:**
  - CWE-298 and CWE-299 are both labelled "…Host Mismatch". Their real names are "Improper Validation of Certificate Expiration" and "Improper Check for Certificate Revocation" (issues #923/#936).
  - Several other entries use outdated CWE names: 201, 256, 328, 329, 526, 653 and 221.
- **The prose disagrees with the lists in places:**
  - The introduction says "248 CWEs"; the lists hold 249.
  - It says A03 has "5 CWEs"; that was before CWE-1357 was added on 2025-12-24 (commit d7059844).
  - It says Injection has "38"; the list has 37.
  - Use the lists and score tables, not the prose.

**Machine-readable versions:**
- **OWASP:** none. The repo holds only Markdown lists; `2025/Data/` has only a sample submission CSV/JSON and README, no mapping or stats file.
- **MITRE:** view **CWE-1450 "Weaknesses in OWASP Top Ten RC1 (2025)"**, built from the release candidate.
  - Page: https://cwe.mitre.org/data/definitions/1450.html
  - XML: https://cwe.mitre.org/data/xml/views/1450.xml.zip
  - CSV: https://cwe.mitre.org/data/csv/1450.csv.zip
  - The category entries are CWE-1436 (A01) to CWE-1445 (A10). In CWE 4.20 (2026-04-30) they match OWASP exactly for 9 of 10 categories.
  - The exception is **A03 (CWE-1438)**, which holds 447, 477, 1035, 1104, 1329 and 1395: it has both 447 and 477 and lacks 1357.
  - MITRE's own note says these were "pulled directly from the CWE mappings cited in the 2025 OWASP Top Ten" and include categories and pillars that are discouraged for mapping.
  - There is no MITRE view for the final edition yet.

### 2. Score tables (from each category page)
Columns: CWEs mapped | max incidence | avg incidence | max coverage | avg coverage | avg weighted exploit | avg weighted impact | total occurrences | total CVEs

| Cat | CWEs | Max inc | Avg inc | Max cov | Avg cov | Exploit | Impact | Occurrences | CVEs |
|---|---|---|---|---|---|---|---|---|---|
| A01 | 40 | 20.15% | 3.74% | 100.00% | 42.93% | 7.04 | 3.84 | 1,839,701 | 32,654 |
| A02 | 16 | 27.70% | 3.00% | 100.00% | 52.35% | 7.96 | 3.97 | 719,084 | 1,375 |
| A03 | 6 | 9.56% | 5.72% | 65.42% | 27.47% | 8.17 | 5.23 | 215,248 | 11 |
| A04 | 32 | 13.77% | 3.80% | 100.00% | 47.74% | 7.23 | 3.90 | 1,665,348 | 2,185 |
| A05 | 37 | 13.77% | 3.08% | 100.00% | 42.93% | 7.15 | 4.32 | 1,404,249 | 62,445 |
| A06 | 39 | 22.18% | 1.86% | 88.76% | 35.18% | 6.96 | 4.05 | 729,882 | 7,647 |
| A07 | 36 | 15.80% | 2.92% | 100.00% | 37.14% | 7.69 | 4.44 | 1,120,673 | 7,147 |
| A08 | 14 | 8.98% | 2.75% | 78.52% | 45.49% | 7.11 | 4.79 | 501,327 | 3,331 |
| A09 | 5 | 11.33% | 3.91% | 85.96% | 46.48% | 7.19 | 2.65 | 260,288 | 723 |
| A10 | 24 | 20.67% | 2.95% | 100.00% | 37.95% | 7.11 | 3.81 | 769,581 | 3,416 |

**"Next Steps" page** (https://owasp.org/Top10/2025/X01_2025-Next_Steps/) has three extra items that are not part of the Top 10:
- **X01 Lack of Application Resilience:** its list is a copy-paste of A06 (open issue #914 / PR #915), although the score table says 16 CWEs. The prose names 400, 409, 674 and 835. Treat this list as unreliable.
- **X02 Memory Management Failures:** 24 CWEs per its table, but only 20 are listed: 14, 119, 120, 121, 122, 124, 125, 126, 190, 191, 196, 367, 415, 416, 457, 459, 467, 787, 788, 824.
- **X03 Inappropriate Trust in AI Generated Code:** the list reads "-none-".

### 3. Overlaps and changes from 2021
- **Overlaps:** none within A01–A10. 2021 had one: CWE-259 was in both A02 and A07.
- **Category changes:**
  - SSRF (A10:2021, CWE-918) is folded into A01.
  - A06:2021 "Vulnerable and Outdated Components" became A03 "Software Supply Chain Failures" (from the community survey).
  - A10 "Mishandling of Exceptional Conditions" is new.
  - Renamed: A07 (dropped "Identification and") and A09 ("Monitoring" became "Alerting").
  - New ranks: Misconfiguration 5→2, Crypto 2→4, Injection 3→5, Insecure Design 4→6.
- **How the 2021 lists carried over:**
  - Same position or renumbered, nearly intact: A01→A01 (28 kept), A02 Crypto→A04 (26), A03 Injection→A05 (26), A04 Design→A06 (29), A05 Misconfig→A02 (14), A07→A07 (19 + 259), A08→A08 (10), A09→A09 (4).
  - Moved: CWE-209, 235 and 280 went from 2021 A04 to A10; CWE-756 went from 2021 A05 to A10.
  - About 85 CWEs are new in 2025. Most of A10 is new, as are 16 in A07, 11 in A01 and 11 in A05.
- **Dropped from 2021 (32 CWEs):** 2, 35, 75, 87, 100, 138, 184, 213, 255, 257, 264, 275, 310, 430, 471, 520, 537, 541, 579, 650, 651, 652, 706, 720, 818, 840, 913, 927, 937, 1032, 1173, 1216.

### 5. Release status
The 2025 edition is **final**.
- OWASP's project page (https://owasp.org/www-project-top-ten/) says "The most current released version is the OWASP Top 10 2025".
- The repo removed the "RC" stylesheet from every 2025 page in commit d4d000ec "Remove RC notice" on **2025-12-24**. The same day it added CWE-1357 to A03 and updated A03's stats.
- RC1 was announced around 6 Nov 2025 at Global AppSec Washington DC. Secondary sources say the final came in January 2026; I found no primary OWASP announcement giving an exact date.

Sources: [OWASP Top 10:2025](https://owasp.org/Top10/2025/), [OWASP/Top10 repo](https://github.com/OWASP/Top10/tree/master/2025/docs/en), [MITRE CWE-1450](https://cwe.mitre.org/data/definitions/1450.html), [issue #907](https://github.com/OWASP/Top10/issues/907), [PR #910](https://github.com/OWASP/Top10/pull/910), [Cyber Security News](https://cybersecuritynews.com/owasp-top-10-2025/), [Penta Security RC1](https://www.pentasecurity.com/?p=32222), [GitLab blog](https://about.gitlab.com/blog/2025-owasp-top-10-whats-changed-and-why-it-matters/).
