# A. Did the screener predict difficulty?

_Round-1 analysis, 2026-10-16. Data: `A-task-outcomes.tsv` (one row per task, 95 columns). The scripts
are in the session scratchpad, not the repo; the method is described in §2. Read-only: nothing in
`sourcer/` or `build/` was changed._

## Bottom line

1. **Only weakly, and not with the current v2 weights.** On the six distinct mined bases, the
   pre-v2 computed score ranked difficulty fairly well: Spearman ρ = +0.66 against our composite
   difficulty. The current v2 computed score is at ρ = −0.06: it puts **russh**, one of the easiest
   tasks, at #28 of 1,462, and **async-http-client**, which produced real defects in both models, at
   #185. With n = 6 this is a direction, not a result.
2. **The stacking screener (`rank_score`) runs backwards.** ρ = −0.63, n = 7. It measures volume and
   ease of building, not difficulty: asyncssh had the lowest rank of the built stacks and was the
   hardest task we have.
3. **Fix size does not predict failure in our setting.** Files, hunks and lines run from ρ ≈ −0.3 to
   +0.1 against fail share and reward loss. Size predicts only *time and tool calls* (ρ up to +0.48),
   i.e. volume. On top of that, S1+S6 hits its cap (7) on **17 of 19** reference fixes, so it cannot
   separate our tasks at all.
4. **Weakness points (S5) run the wrong way at item level.** Of the 44 real flaws we built, the 9
   with S5 ≥ 2 were fixed in every clean run (0/9 failed). Real defects hit 6 of the 35 flaws with
   S5 ≤ 1, at p = 0.23. Every failed item is A01, A07 or unmapped (863, 862, 287, 601, 835). None
   was among the "hard across sources" CWEs (345, 494, 613, 770, 522).
5. **What did separate hard from easy is not in the screener.** Real defects (19 runs on 8 tasks,
   listed in §1) fall into four kinds:
   - a site or path the instruction did not name: the jackson any-setter siblings, argo's
     `spec.templateDefaults`;
   - over-broad fixes that broke a nearby legitimate behaviour: 7–8 jackson-family runs, webob;
   - an adjustment next to the fix site that reorders the guard: asyncssh, dropbear `-= 1`;
   - edge semantics or fail-open fallbacks: async-http-client's cookie decode, rclone's
     access-key/md5 fallback.

   The cleanest contrast is inside one base:
   - jackson-databind-sib, siblings not named: DeepSeek 0/6;
   - jackson-sib7, siblings named: DeepSeek 8/11;
   - rclone-sib and russh-sib, every site named: both models solved them cleanly.
6. **Evidence is thin everywhere.** There are 19 tasks, but the hard set rests on about 5
   independent bases, and the jackson family supplies 3 of the top 9. Every ρ here has a
   permutation p > 0.05, apart from features that only mark the jackson family (Java, v1 score).
   Read every number as a rank-order description.

## 1. Data and definitions

- **Units:**
  - 19 trialled tasks: 7 mined, 8 stacking, 4 injection;
  - 38 (task, model) pairs;
  - 186 raw trials, classified run by run with the same rules as `build/audit_results.py` (its
    functions imported; the internet-use cache only read).
- **Primary outcome (offline era).** Only 22 of 38 pairs have an offline-era run: DeepSeek 13,
  MiMo 9. All six jackson-family pairs, py-shiny and cloudreve have none. So the working sample
  is the **no-lookup set**:
  - offline-era runs;
  - plus online-era runs that made no internet lookup (by `internet_use.hits`).

  This is the set the ledger itself counts. Statuses kept: counted or awaiting-audit. Dropped:
  test-fault, provider-stop, leaked answer or tests, grader-fault, untrusted, ungraded and
  user-stopped runs. Offline-era columns are reported separately (`*_off_*`).
- **Other run groups:**
  - Online-era runs with a lookup are in `*_online_lookup_*`. They solved **38/38** (DeepSeek
    31/31, MiMo 7/7), against 62/79 for no-lookup runs.
  - Online runs cut at 60 min without a solve are kept out of the solve rates, as the ledger does,
    and counted in `*_nolookup_cut60_nonsolves`.
- **Difficulty signals per task.** Fail share and reward loss are averaged over the two models.
  Time to solve and tool calls to solve are per-model percentile ranks, averaged; an unsolved pair
  ranks slowest. Plus "any real defect". The **composite** is the mean of the percentiles of
  reward loss, time, tool calls and defect.
- **Real defect.** A run that lost reward to a fault in its own code, on a test judged fair:
  - the postmortem items marked `genuine-fail`;
  - the regrade and fairness findings listed in CONTEXT.md.

  19 runs on 8 tasks are listed in `REAL_DEFECT` in the build script. rclone r11 (`rEMTRVZ`) is a real defect
  but sits in the leaked-contract era, so it is listed and not counted in the no-lookup sample.
- **Screener values:**
  - mined: re-scored with the **current** `weights.json` by importing `osv_sourcer`
    (`compute_signals`, `score_entry`) over a read-only connection to `index/candidates.sqlite`;
  - injected tasks inherit their base's score (marked `inh.`);
  - stacking: `rank_score` from `stacking-shortlist.tsv` / the manifest (cloudreve v4 is not on
    the shortlist);
  - reference-fix shape: `patchmetrics.parse_patch` on `tasks/<t>/solution/fix.patch`, scored with
    the current S1+S6 weights;
  - taxonomy labels: `weakness_points()` on the task's CWE list.

## 2. Per-task table

Each model cell reads: offline solved/n · no-lookup solved/n · no-lookup mean reward · median
minutes to solve · median tool calls to solve · online-with-lookup solved/n · real-defect runs. The
screener score is computed/read: v2 (current weights), then the v1 shortlist values.

| Task | Track | Lang | CWEs (task) | Sev | OWASP | S5 pts | Screener score | Sec/Fn tests | Flaws | Ref fix files/hunks/lines | Same-check sites | DeepSeek | MiMo | Composite |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| async-http-client | mined | Java | 287 | MOD | A07 | -1 | v2 13/20 (v1 15/24) | 6/6 | 1 | 3/10/107 | 2 | 0/0 · 1/2 · 0.917 · 65 · 155 · 1/1 · 1 | 3/3 · 3/3 · 1.0 · 76 · 135 · 0/0 · 1 | 0.66 |
| hickory-dns | mined | Rust | 347 | HIGH | A04 | 1 | v2 8/18 (v1 7/20) | 7/11 | 1 | 4/8/50 | 1 | 1/1 · 1/1 · 1.0 · 25 · 205 · 1/1 · 0 | 0/0 · 1/1 · 1.0 · 62 · 141 · 0/0 · 0 | 0.38 |
| jackson-databind | mined | Java | 863 | MOD | A01 | 0 | v2 15/22 (v1 19/26) | 5/9 | 1 | 1/4/111 | 4 | 0/0 · 2/3 · 0.667 · 38 · 128 · 0/0 · 1 | 0/0 · 3/3 · 1.0 · 59 · 96 · 0/0 · 0 | 0.57 |
| py-shiny | mined | Python | 22 | MOD | A01 | 0 | – (no index score) | 6/6 | 1 | 5/12/107 | 2 | 0/0 · 10/10 · 1.0 · 5 · 73 · 11/11 · 0 | 0/0 · 1/1 · 1.0 · 29 · 113 · 0/0 · 0 | 0.19 |
| rclone | mined | Go | 287 | CRIT | A07 | -1 | v2 10/17 (v1 13/17) | 10/5 | 1 | 3/17/292 | 2 | 1/1 · 1/1 · 1.0 · 15 · 139 · 0/0 · 1* | 1/1 · 1/1 · 1.0 · 64 · 112 · 0/0 · 0 | 0.42 |
| russh | mined | Rust | 129 | LOW | A05 | 1 | v2 17/20 (v1 12/20) | 12/10 | 1 | 2/2/45 | 1 | 1/1 · 1/1 · 1.0 · 27 · 188 · 2/2 · 0 | 0/0 · 2/2 · 1.0 · 66 · 92 · 0/0 · 0 | 0.36 |
| webob | mined | Python | 601 | MOD | A01 | 1 | v2 15/20 (v1 11/19) | 9/9 | 1 | 4/10/177 | 1 | 2/2 · 2/2 · 1.0 · 12 · 75 · 0/0 · 0 | 1/2 · 1/2 · 0.5 · 41 · 76 · 0/0 · 1 | 0.46 |
| actualbudget | stacking | TS | 306,862,863,22,284,285,613 | max CRIT | A07 | 3 | rank 30.2 | 15/13 | 6 | 6/21/208 | 9 | 1/1 · 1/1 · 1.0 · 9 · 99 · 1/1 · 0 | 0/0 · 1/1 · 1.0 · 28 · 85 · 2/2 · 0 | 0.18 |
| argo-workflows | stacking | Go | 862,863,200,522,770 | max HIGH | A06 | 2 | rank 30.1 | 17/10 | 5 | 8/21/168 | 3 | 1/2 · 1/2 · 0.853 · 47 · 221 · 1/1 · 1 | 1/2 · 1/2 · 0.853 · 77 · 157 · 1/1 · 1 | 0.74 |
| asyncssh | stacking | Python | 22,287,345,354,639,835 | max HIGH | A08 | 4 | rank 26.2 | 12/5 | 4 | 3/20/136 | 7 | 0/1 · 0/1 · 0.917 · – · – · 2/2 · 1 | 1/1 · 1/1 · 1.0 · 96 · 213 · 1/1 · 0 | 0.85 |
| cloudreve | stacking | Go | 863,22,200,359,400,770 | max MOD | A06 | 2 | – (v4 not shortlisted) | 5/7 | 5 | 6/15/74 | 2 | 0/0 · 1/1 · 1.0 · 17 · 183 · 0/0 · 0 | 0/0 · 1/1 · 1.0 · 60 · 158 · 0/0 · 0 | 0.37 |
| filament | stacking | PHP | 862,204,294,306 | max MOD | A07 | 1 | rank 29.2 | 8/7 | 4 | 9/23/177 | 2 | 1/1 · 1/1 · 1.0 · 48 · 358 · 5/5 · 0 | 1/1 · 1/1 · 1.0 · 84 · 293 · 1/1 · 0 | 0.58 |
| ruby-saml | stacking | Ruby | 347,287,400,770 | max CRIT | A06 | 3 | rank 31.0 | 5/6 | 3 | 2/4/34 | 1 | 1/1 · 1/1 · 1.0 · 16 · 96 · 1/1 · 0 | 1/1 · 1/1 · 1.0 · 64 · 144 · 1/1 · 0 | 0.31 |
| stigmem | stacking | Python | 862,285,863,319,489,494,770,732 | max CRIT | A06 | 4 | rank 35.0 | 9/8 | 6 | 11/36/349 | 2 | 1/1 · 1/1 · 1.0 · 54 · 254 · 2/2 · 0 | 0/0 · 2/2 · 1.0 · 87 · 208 · 0/0 · 0 | 0.57 |
| trigger-dev | stacking | TS | 918,639,306,862 | max HIGH | A07 | 1 | rank 32.0 | 13/7 | 4 | 7/17/329 | 1 | 1/1 · 1/1 · 1.0 · 40 · 360 · 3/3 · 0 | 1/1 · 1/1 · 1.0 · 86 · 226 · 1/1 · 0 | 0.57 |
| jackson-databind-sib | injection | Java | 863 | MOD | A01 | 0 | v2 15/22 inh. | 8/15 | 2 (sibling not named) | 2/8/141 | 7 | 0/0 · **0/6** · 0.312 · – · – · 0/0 · 6 | 0/0 · 1/2 · 0.5 · 44 · 173 · 0/0 · 1 | 0.82 |
| jackson-sib7 | injection | Java | 863 | MOD | A01 | 0 | v2 15/22 inh. | 10/20 | 4 (forms listed) | 3/9/148 | 8 | 0/0 · 8/11 · 0.773 · 26 · 165 · 0/0 · 3 | 0/0 · 2/3 · 0.667 · 42 · 154 · 0/0 · 1 | 0.64 |
| rclone-sib | injection | Go | 287 | CRIT | A07 | -1 | v2 10/17 inh. | 16/12 | 5 (all named) | 6/21/333 | 2 | 1/1 · 1/1 · 1.0 · 21 · 210 · 0/0 · 0 | 1/1 · 1/1 · 1.0 · 81 · 159 · 0/0 · 0 | 0.46 |
| russh-sib | injection | Rust | 129† | LOW | A05 | 1 | v2 17/20 inh. | 17/11 | 3 (all named) | 1/2/51 | 1 | 1/1 · 1/1 · 1.0 · 38 · 160 · 1/1 · 0 | 0/0 · 2/2 · 1.0 · 67 · 123 · 0/0 · 0 | 0.39 |

\* rclone/DeepSeek's real defect is in an excluded run (task leaked the contract).

† russh-sib's true weakness is CWE-287/345/354, mislabelled 129 upstream. Under the correct labels
it would score S5 = 4 (A08, CWE-345 +2), and it was one of the cleanest solves.

**Composite ranking, hardest first:**

1. asyncssh 0.85
2. jackson-databind-sib 0.82
3. argo 0.74
4. async-http-client 0.66
5. jackson-sib7 0.64
6. filament, stigmem, trigger-dev and jackson-databind, at about 0.57

The three stacks in place 6 are "slow and long" with no defect; jackson-databind is "fast" with
one over-broad failure. Easiest: actualbudget 0.18, py-shiny 0.19.

## 3. Which features separate harder tasks

### Spearman ρ, feature vs difficulty (19 tasks unless noted; + means the feature is higher on harder tasks)

| Feature | Fail share | Reward loss | Time to solve | Tool calls | Real defect | Composite | Perm. p (composite) |
|---|---|---|---|---|---|---|---|
| S5 weakness points (current weights) | −0.09 | −0.22 | +0.20 | +0.21 | −0.32 | −0.11 | 0.66 |
| OWASP category points | −0.17 | −0.38 | +0.45 | +0.38 | −0.23 | +0.07 | 0.77 |
| A01 is the best category | +0.48 | +0.67 | −0.45 | −0.35 | +0.46 | +0.11 | 0.66 |
| CWE Top 25 label | +0.20 | +0.16 | +0.07 | +0.30 | −0.01 | +0.20 | 0.43 |
| Attack label (credential-access / Collect info) | +0.16 | +0.10 | +0.29 | +0.48 | +0.18 | +0.42 | 0.08 |
| Severity (ordinal) | −0.22 | −0.30 | +0.03 | +0.11 | −0.11 | −0.06 | 0.82 |
| Reference fix files | −0.25 | −0.32 | +0.17 | +0.37 | −0.33 | +0.08 | 0.74 |
| Reference fix hunks | −0.08 | −0.20 | +0.29 | +0.41 | −0.09 | +0.26 | 0.26 |
| Reference fix lines | +0.02 | +0.03 | +0.19 | +0.25 | +0.12 | +0.33 | 0.15 |
| S1+S6 points on the reference fix | +0.25 | +0.25 | −0.10 | +0.14 | +0.29 | +0.28 | 0.27 (17/19 at the cap) |
| Same-check sites (reference fix) | +0.54 | +0.49 | −0.04 | +0.13 | +0.48 | +0.41 | 0.08 |
| Flaws to close | −0.09 | −0.19 | +0.24 | +0.48 | −0.30 | +0.15 | 0.55 |
| Security tests | +0.03 | −0.08 | +0.23 | +0.20 | −0.03 | +0.16 | 0.50 |
| Java | +0.61 | +0.72 | +0.01 | −0.04 | +0.61 | +0.47 | 0.05 |
| Prescore ecosystem points | +0.19 | +0.27 | +0.03 | −0.03 | +0.21 | +0.13 | 0.59 |
| Injected sibling not named by the instruction | +0.54 | +0.62 | −0.13 | +0.19 | +0.40 | +0.41 | 0.11 |
| Stacking `rank_score` (n = 7) | −0.63 | −0.58 | −0.21 | −0.43 | −0.63 | −0.63 | 0.14 |
| Stacking mean item S5 (n = 8) | +0.25 | +0.23 | +0.38 | +0.05 | +0.25 | +0.19 | 0.63 |

### Mined bases only (n = 6; with "family" collapsed, each sib task is averaged into its base)

| Score | ρ composite | ρ composite (family) | ρ reward loss (family) | Rank of the mined tasks |
|---|---|---|---|---|
| v1 computed (shortlist) | +0.66 | +0.71 | +0.52 | jackson 19, ahc 15, rclone 13, russh 12, webob 11, hickory 7 |
| v1 read | +0.46 | +0.52 | +0.52 | |
| **v2 computed (current)** | **−0.06** | +0.03 | +0.37 | russh 17, jackson 15, webob 15, ahc 13, rclone 10, hickory 8 |
| v2 read | +0.46 | +0.58 | +0.81 | |

**Why v2 computed fell:**

- **CWE-287 "saturated" (−2)** demoted async-http-client and rclone. async-http-client produced
  real defects in both models; rclone produced one in DeepSeek.
- **The new S6 points lifted russh.** S6 was raised to +2 for files, +2 for hunks and +1 for 50+
  lines. That lifts tasks *without* S1, because tasks with S1 were already at the cap. russh has
  no S1 and is easy: about 27 min for DeepSeek, solved by MiMo in both runs.
- **Wording-only signals add 8 points to russh.** S2 hint +2, S3 +3 and S4 "earlier fix
  incomplete" +3 fire on 4 of the 6 mined bases. Two are hard (jackson, async-http-client) and two
  are easy (russh, webob), so they separate nothing.
- **The reader judgements cannot discriminate.** S1/S2/S3 = "yes" on every trialled shortlist
  task except rclone's S1. With no variance they cannot be tested on our data.

### Item level (44 real flaws: 7 mined + 37 stacking items)

| Group | Items | With a real defect in a clean run | Which |
|---|---|---|---|
| S5 ≥ 2 | 9 | 0 | – |
| S5 ≤ 1 | 35 | 6 | jackson 863; ahc 287; webob 601 (functional); argo sync 862/863; argo ref-mode 863; asyncssh pktsize 835 |
| OWASP A01 | 17 | 4 | jackson, webob, argo ×2 |
| Not A01 | 27 | 2 | ahc (A07), asyncssh (unmapped) |

- **S5:** the hypergeometric p for 0 of 9 is 0.23.
- **A01:** p for ≥ 4 of 6 failures falling in A01 is 0.14.
- **Caveat on stacking items:** each stacking instruction lists its items. Localisation is
  therefore given away, so the weakness labels are tested only for "can the model fix a flaw it
  has been told about".

### Group contrasts (Cliff's δ on the composite; + means harder)

| Feature | Groups | Cliff's δ | Note |
|---|---|---|---|
| Same-check sites ≥ 4 | 5 vs 14 | +0.40 (fail share +0.63) | the jackson family, asyncssh and actualbudget. actualbudget has 9 sites and is the easiest task: they were *named*. |
| Java | 4 vs 15 | +0.67 | every Java task had a real defect, but 3 of the 4 are one base |
| Severity CRITICAL / max CRITICAL | 5 vs 14 | −0.44 | critical tasks are easier, as the literature found (+4.7 pts) |
| Fix files ≥ 4 | 10 vs 9 | −0.24 (defect −0.47) | bigger fixes had *fewer* defects |
| Stacking vs the rest | 8 vs 11 | +0.09 | stacking has a higher time percentile (+0.39) and a lower defect rate (−0.30): volume, not difficulty |

## 4. Against the literature (research/*findings.md)

| Literature claim → weight | Our data | Verdict |
|---|---|---|
| Fix shape is the strongest predictor (PatchEval) → S6 +2/+2/+1 | Size tracks time and tool calls only; failures went the other way. Range restriction: 17 of 19 tasks have ≥ 2 files, so the PatchEval contrast (1 file vs 3+) is not testable. | **Contradicted inside the shortlist band.** Consistent with SEC-bench and "Beyond Resolution Rates" (size does not predict). Keep −3 for a single compact hunk as a filter. |
| Localisation / symptom–fix disparity is the main failure (S2) | Failures were "unnamed second site / alternate path" (jackson siblings, argo templateDefaults) and wrong-object checks (argo sync). That is localisation in the broad sense. The S2 *wording hint* fired on easy russh and webob and missed jackson. | **Supported in substance; the wording proxy is not.** The computed S2 (§7 of owasp findings) is still untested. |
| Injected variants drop models to 0–20% (Garg) | jackson-databind-sib DeepSeek 0/6 (the only genuine failure). But rclone-sib and russh-sib, with every sibling named, were easy. | **Supported only when the siblings are not disclosed.** |
| A01 easiest, A08/A06 hardest (CWE-bench) | A01 items carried 4 of 6 defects; the A08 items (345, 354, 494) never failed. | **Contradicted at item level** (n small, p = 0.14). The CWE-bench extremes rest on 11–13 tasks per category. |
| CWE-287 saturated (−2; CWE-bench, 1 task) | async-http-client: real defects in both models. rclone: a DeepSeek defect (leaked era). Both still solved in the end. | **Contradicted** (2 of 3 CWE-287 bases). |
| CWE-22 disputed (0) | py-shiny is the easiest task (DeepSeek 5 min, 10/10). Path-traversal items in asyncssh, cloudreve and actualbudget never failed. | Leans **easy**: supports 0 or −1. |
| CWE-347 a DeepSeek weak spot (+1) | hickory: DeepSeek 25 min offline. ruby-saml (347): DeepSeek 16 min. | **Not supported** (2 tasks). |
| CWE-601 hard in CWE-bench (+1) | webob: DeepSeek fast. MiMo 1 of 2 offline with a functional regression (over-broad), not a security miss. | Mixed. |
| 345/494/613 hard across sources (+2) | Items in asyncssh, stigmem and actualbudget, plus russh-sib's true label: all fixed in every clean run. | **Not supported**, but the items were named by the instruction. Can't separate. |
| Abstract-only CWEs +1 | No trialled task is abstract-only. | Cannot test. |
| LLM-in-the-loop +2 | No trialled task. | Cannot test. |
| Top 25 easier (label only) | ρ ≈ +0.2 (harder), with almost no variance (12 of 19 labelled). | Cannot test; keep the label. |
| Attack label credential-access / Collect info (label only) | Composite δ +0.60, p = 0.08, driven by time; the unlabelled side holds asyncssh (hardest). | Inconclusive; keep the label. |
| CVSS: high/critical slightly *easier* | Critical tasks easier (δ −0.44). | **Consistent**; keep it descriptive. |
| Java and Rust weakest for DeepSeek → prescore Maven 3, crates.io 3 | Java 4/4 tasks with defects (one family dominates). Rust 0/3 (two share a base). | Maven supported, crates.io contradicted; both weak. |
| No MiMo data published | MiMo's only defects: webob regression, argo sync/templateDefaults, async-http-client (cut run), jackson-sib over-broad. MiMo never missed the siblings that DeepSeek dismissed. | First MiMo evidence: MiMo probes; its errors are over-broad or semantic, not missed sites. |

## 5. Proposed weight changes (NOT applied)

The proposal is fit **in-sample on 6 mined bases**, so it is a hypothesis for round 2, not a
validated improvement. On the full index (1,462 candidates), a re-score with these weights:

| | ρ composite (6 mined bases) | Top-20 overlap with current | Top-50 | Top-100 |
|---|---|---|---|---|
| Current v2 | −0.06 | – | – | – |
| Proposed (without A01) | +0.76 | 13 | 36 | 78 |
| Proposed (with A01) | +0.79 | 13 | 35 | 80 |

**Rank changes under the proposal** (with the A01 change in brackets):

| Task | Current rank | Proposed rank |
|---|---|---|
| russh | #28 | #226 |
| webob | #84 | #224 |
| jackson-databind | #85 | #75 (#45) |
| async-http-client | #185 | #133 |
| rclone | #469 | #225 |

```diff
--- sourcer/weights.json (current v2)
+++ sourcer/weights.json (proposed v3)
@@ cause_other_layer
-    "advisory_hint": 2
+    "advisory_hint": 1
@@ defence_ineffective
-    "advisory_and_condition_rewritten": 3,
+    "advisory_and_condition_rewritten": 2,
@@ bypass_and_siblings
-    "earlier_fix_incomplete": 3,
+    "earlier_fix_incomplete": 2,
@@ weakness.category_points          (OPTIONAL, weakest item; conflicts with CWE-bench)
-      "A01": 0,
+      "A01": 1,
@@ weakness.cwe_adjustments.disputed.cwes
-        "cwes": [22, 79, 94, 918],
+        "cwes": [22, 79, 94, 287, 918],
@@ weakness.cwe_adjustments.saturated.cwes
-        "cwes": [285, 287, 319, 330, 434, 470, 916, 1104],
+        "cwes": [285, 319, 330, 434, 470, 916, 1104],
@@ fix_shape
-    "two_plus_files": 2,
-    "three_plus_hunks": 2,
+    "two_plus_files": 1,
+    "three_plus_hunks": 1,
     "three_plus_hunks_far_apart": 1,
-    "fifty_plus_changed_source_lines": 1,
+    "fifty_plus_changed_source_lines": 0,
     "code_deleted_or_restructured": 1,
     "single_compact_hunk": -3,
@@ overbroad_repair
-    "judged": 2
+    "judged": 3,
+    "_note": "S7: also yes when a nearby LEGITIMATE behaviour (linked/permitted property, protocol-relative URL, loopback setup) must keep working"
@@ prescore.ecosystem_points
-      "crates.io": 3,
+      "crates.io": 2,
+  "undisclosed_siblings": {
+    "_note": "S8 NEW. The same trust decision recurs at sites the advisory and upstream fix do not name (other call sites of the guard or sink at the vulnerable commit; alternate path to the same sink). Judged now; computed later by a repository search.",
+    "judged": 3,
+    "computed_other_call_sites_2plus": 2
+  },
+  "upstream_fix_public": {"points": 0, "_note": "label: 0 offline; -2 for any trial setting with internet (lookup runs solved 38/38)"},
+  "adjacent_adjustment_logic": {"points": 0, "_note": "label: guard must sit before/after a value adjustment at the fix site (asyncssh dropbear -= 1); n = 1, score once n >= 3"}
```

### Evidence and strength per change

| Change | Evidence | Strength |
|---|---|---|
| CWE-287 out of saturated, into disputed (−2 → 0) | 2 of 3 CWE-287 bases produced real defects (async-http-client in both models; rclone in DeepSeek). The CWE-bench "100%" rests on 1 task. Explains most of v2's demotion of async-http-client and rclone. | **Moderate** (direct, but 3 tasks) |
| S6 positives halved; 50+ lines → 0 | ρ(size, failure) ≈ 0 or negative on 19 tasks; size tracks only time and tool calls. The S1+S6 cap binds on 17 of 19, so S6 can't rank inside the band. S6's v2 increase is what lifted russh above async-http-client. | **Moderate** for "no failure signal inside the band"; PatchEval's 1-vs-3+ file effect is untested by us, so keep −3 for a compact hunk |
| Wording-only S2/S3/S4 reduced by 1 each | They fire on 4 of 6 mined bases, hard and easy alike; they gave russh (easy) the top v2 score | **Weak** (n = 6) |
| S7 judged 2 → 3, wider definition | Over-broad or regression faults: 7–8 jackson-family runs (both models), webob MiMo. S7 = yes on jackson; webob was "no" but had the same failure kind. | **Weak–moderate** |
| A01 0 → 1 (optional) | A01 items carried 4 of 6 defects (p = 0.14). It contradicts CWE-bench's stable "A01 easy" extreme. | **Weak**: apply only if round 2 repeats it |
| crates.io prescore 3 → 2 | 3 Rust tasks, all clean (2 share a base) | **Weak** |
| No change: 345/494/613 +2, 347 +1, 601 +1 | Not confirmed by us (0 failures), but every item was named by its instruction | Can't test; revisit with undisclosed items |
| No change: Top 25 and attack labels at 0 | No usable variance or signal | Can't test |
| Stacking `rank_score` | ρ = −0.63 (n = 7); it ranks build ease and volume. Not in `weights.json`. | Don't read it as difficulty; choose stacks by item-level S8/S7 |

## 6. New features worth adding

1. **S8: undisclosed siblings / alternate paths** (proposed +3 judged, +2 computed). This is the
   strongest within-base evidence we have:
   - jackson-databind-sib, sibling not named: DeepSeek 0/6, all six dismissing the any-setter path;
   - jackson-sib7, forms listed in the instruction: DeepSeek 8/11;
   - rclone-sib and russh-sib, all sites named: both models solved cleanly;
   - argo's `spec.templateDefaults`, a second route to the same pod fields, failed both models' r11
     runs.

   **Computable:** the guard and sink names are already in `shape.same_check_name`. Searching the
   vulnerable commit for other call sites the fix did not touch gives a count. This is what
   owasp_top10_findings §7 calls the "heavier, later step"; our data says it is the step that
   matters.
2. **Number of independent call sites.** It only matters when the sites are *not named*:
   - actualbudget, 9 same-check sites, named: easiest task;
   - jackson-sib, 7 sites, not named: genuine failure.

   Fold it into S8 rather than scoring raw counts.
3. **Upstream fix public and findable** (label). It is not a difficulty signal offline. Any
   internet-enabled run (TB3's default) makes it decisive: lookup runs solved 38/38, against
   62/79 without a lookup. The only genuine failure was on code with no upstream fix.
4. **Adjacent adjustment logic at the fix site** (label). asyncssh's dropbear `-= 1` turned a
   correct-looking `== 0` guard into a hang. That is n = 1 (the hardest task). Record it per
   candidate and score it once ≥ 3 cases exist.
5. **Fail-open fallback or default branch** (label): rclone fell back to the access key ID / md5
   when the proxy returned no secret. n = 1.
6. **Instruction disclosure is a builder lever, not a screener feature.** Rules from round 1:
   - never enumerate sibling sites or forms in the instruction;
   - the stacking track's enumeration of items is why stacks added time but not difficulty.

## 7. Limits

- **Small and clustered sample.** 19 tasks, about 5 independent hard bases; the jackson family
  is 3 of the top 9.
- **Thin offline coverage.** Only 22 of 38 pairs have an offline-era run. The no-lookup sample
  mixes 60-min and 120-min limits.
- **Run counts vary hugely:** py-shiny has 21 DeepSeek runs, many pairs have 1. Solve rates for
  n = 1 pairs are 0 or 1, which is why time and tool calls carry most of the signal.
- **Tests in flux.** Repaired tests changed rewards today: argo, asyncssh, async-http-client,
  webob. trigger-dev's repair is still running, so its row may move.
- **Fit in sample.** The proposed weights are fit on the same 6 bases they are scored on.
  Validate on round-2 tasks before applying.
