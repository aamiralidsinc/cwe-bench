# Taxonomy research plan

_Created 2026-10-15. Status: **plan only; no research done yet.** It lists what we will
research, the question for each item, and how each result will be used. Background on the
taxonomies themselves: [taxonomy.md](taxonomy.md)._

**The rule for every item:**
- **If public evidence exists** linking the taxonomy to LLM failure, use it directly in the
  screening score (`sourcer/weights.json`).
- **If it doesn't,** generate the evidence from our own trial results (per task, per model),
  then use it in the screening score.

Some items are also used for **experiment planning** (stacking, sibling injection, test
variants), not only for scoring.

---

## 0. Which taxonomy we use, and how

- **Primary classification: OWASP Top 10:2025**, the same as CWE-bench, so our results line
  up with how CWE-bench reports and how the client reads results.
- **Leaf level: MITRE CWE IDs** (each task already records them in `task.toml`). The CWE
  hierarchy gives finer detail under each OWASP bucket.
- **Extra layers** (severity, exploitation, attack patterns) become **scoring dimensions**
  and analysis variables, not classifications.

---

## 1. OWASP Top 10:2025: rank, dissect, and weight the categories

**What we will do:**
1. **Dissect each category** at CWE level: within category X, which CWEs (and which kinds of
   fix) the models actually fail.
2. **Drop the easy areas:** remove CWEs or sub-areas where LLMs score about 90% or more. For
   example, CWE-bench reports A04 Cryptographic Failures as the easiest category (Claude Opus
   5.5 at 90%).
3. **Rank the 10 categories** by LLM failure rate.
4. **Add the rank as a scoring dimension** in `sourcer/weights.json`. It replaces or refines
   the current hand-set `weakness_class` mapping.
5. **Pyramid ordering for trials:** start each trial round with candidates from OSV in the
   categories where LLMs fail most, so the first results are strong and quality tapers
   gradually, a pyramid rather than an inverted one.

**Research questions:**
- What is CWE-bench's per-category (and, where available, per-CWE) pass rate for each model?
  The per-category heatmap (Figure 5) is an image; we need the numbers.
- Within each category, which CWEs drive the failures?
- Do our own per-model results agree with CWE-bench's ranking?

**Feeds:** `weights.json` (category rank weight), candidate ordering in the shortlist.

---

## 2. What's wrong in the code? (weakness taxonomies)

### MITRE CWE (hierarchy: Pillar → Class → Base → Variant)
- **Research question:** is there public data on LLM strength or weakness **per CWE** (or
  per CWE class), for fixing or for detecting vulnerabilities?
- **If yes:** add a per-CWE prior to the screening score.
- **If no:** map our own per-task, per-model results onto the CWE hierarchy and build the
  prior ourselves, then add CWE scoring to the screening script so the next candidate
  search uses it.

### CWE Top 25 (yearly, latest 2025)
- **Research question:** do LLMs fail more or less often on Top 25 weaknesses than on rarer
  ones? Is there any published comparison?
- **Use:** a realism/priority signal (common, real-world weaknesses are more defensible to
  the client), plus a failure signal if the evidence supports one.

---

## 3. Which specific bug? (CVE / GHSA / OSV)

- **Not a taxonomy:** these are the identifiers and our source of candidates. Each record links
  to a CWE, and through it to an OWASP category.
- **Plan:** when sourcing from OSV, attach each candidate's CWE, OWASP category, CVSS, EPSS
  and KEV status, so every scoring dimension below can be computed at screening time.

---

## 4. How bad is it? (severity and exploitation)

| Item | What it measures |
|---|---|
| **CVSS (v3.1, v4.0)** | severity score |
| **EPSS** | probability the vulnerability will be exploited |
| **CISA KEV** | whether it is known to be exploited in the wild |

**Research questions, for each of the three:**
- Is there any published LLM evaluation relating this score to LLM failure? For example:
  does higher severity raise or lower the chance an LLM fails to fix it? Is there no
  correlation? Or has nobody studied it?
- Same for EPSS (higher exploitation probability → more or less LLM failure?) and for KEV
  status (known-exploited vs not).

**Plan:**
- **If a relation is proven publicly:** use it as a scoring dimension directly.
- **If not:** record CVSS, EPSS and KEV for every task we trial, test the relation on our own
  per-model results, and add the dimension to the score only if our data supports it. Until
  then, keep them as analysis variables.

---

## 5. How is it attacked? (attack taxonomies)

| Item | What it covers |
|---|---|
| **MITRE CAPEC** | attack patterns, each linked to the CWEs it exploits |
| **MITRE ATT&CK** | adversary behaviour (tactics, techniques) |
| **STRIDE** | threat-modelling classes (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege) |

**Research question:** is there public evidence linking any of these (attack pattern,
technique, STRIDE class) to LLM failure at fixing vulnerabilities?

**Plan:**
- **If there is evidence:** use it in scoring.
- **If not:** tag our tasks with these labels, generate the evidence from our results, then use
  it in scoring.
- **Experiment planning (whatever the evidence):**
  - **Vulnerability stacking:** choose co-present vulnerabilities from *different* attack
    patterns or STRIDE classes, so one fix cannot cover them all.
  - **Sibling injection:** use CAPEC patterns linked to the same CWE to design siblings
    that the same attack reaches through different code paths.
  - **Security tests:** use the CAPEC patterns for a CWE as a checklist of exploit
    variants beyond the original PoC.

---

## 6. How this could help us (to discuss)

- **CWE's hierarchy for siblings.** It gives an exact definition of "same class, different
  variant": siblings could be chosen as different Base/Variant CWEs under the same Class.
  That's more principled than our current same-trust-decision rule.
- **CWE's hierarchy for breadth.** We could measure coverage at several levels (pillar,
  class, base) instead of only the 10 OWASP buckets, and spot that we're all A01/A07 at a
  glance.
- **CAPEC for exploit variants.** Each CWE links to the attack patterns that exploit it, a
  ready-made checklist for the "variants beyond the PoC" our security tests need.
- **Top 25 and KEV for realism and priority.** Weaknesses that are common and actually
  exploited make tasks more defensible to the client.

---

## 7. Tracker

| # | Item | Research question (short) | Status | Feeds into |
|---|---|---|---|---|
| 1 | OWASP Top 10:2025 | Per-category and per-CWE LLM pass rates; drop the ~90%+ areas; rank the 10 | **findings done** (repair-benchmark part pending): [research/owasp_top10_findings.md](research/owasp_top10_findings.md) | S5 screener proposal in that file; pyramid ordering |
| 2a | MITRE CWE | Public per-CWE LLM strength data? | **done**: yes (collected in item 1); hierarchy wired in: [research/cwe_hierarchy_top25_findings.md](research/cwe_hierarchy_top25_findings.md) | per-CWE adjustments, ancestor category fallback, broad-CWE bonus in `weights.json` |
| 2b | CWE Top 25 | Top 25 vs rare CWEs: different LLM failure? | **done**: Top 25 CWEs are *easier* (DeepSeek 67% vs 52%); **decided: label only (0 points)**, revisit with our own trial data | `weakness.top25_label` in `weights.json` (921 candidates labelled) |
| 3 | CVE / GHSA / OSV | (enrichment, not research) | not started | candidate fields at sourcing |
| 4a | CVSS | Severity vs LLM failure: published relation? | **done**: never published; our 13-source analysis: high/critical slightly *easier* (+4.7 pts, p = 0.026, fragile): [research/severity_findings.md](research/severity_findings.md) | none: record only, no score |
| 4b | EPSS | Exploitation probability vs LLM failure? | **done**: no relation (+0.9 pts, p = 0.65) | none: record only |
| 4c | CISA KEV | Known-exploited vs LLM failure? | **done**: untestable, 5 of 922 benchmark CVEs in KEV | none: record only (realism label at most) |
| 5a | CAPEC | Attack pattern vs LLM failure? | **done**: never published; ours: *Collect and Analyze Information* fixed 8–13 pts less (q < 0.05 in 3 of 5 variants), other mechanisms null: [research/attack_taxonomies_findings.md](research/attack_taxonomies_findings.md) | **decided: label only (0 points)**, `weakness.attack_label` in `weights.json` (855 of 1,464 scored candidates labelled); sibling/test-variant checklist |
| 5b | ATT&CK | Technique vs LLM failure? | **done**: *credential-access* tactic fixed 13–21 pts less (q < 0.05 in 3 of 5 variants) but via a noisy CWE→CAPEC→ATT&CK chain and null in LiveCVEBench | same label as 5a (credential-access) |
| 5c | STRIDE | Threat class vs LLM failure? | **done**: no relation; most CWEs get 3+ letters | none; stacking design only |

**When public evidence is missing:** our own data is small (19 tasks today). Any relation we
compute must report its sample size, and must count per model (DeepSeek and MiMo separately),
because the two models fail on different things.
