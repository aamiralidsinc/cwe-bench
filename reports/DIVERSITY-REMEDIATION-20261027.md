# Diversity remediation: checking the diversity report and what to do (2026-10-27)

**Internal only.** Never copy this report to the client repo.

**What this checks:** `reports/DIVERSITY-AND-PATTERNS-20261027.md`.

**Data used:**
- the VM ledger `build/audit/ledger.md` (generated 2026-10-27 18:11; 1,095 raw trials; 241 tasks);
- task metadata `tasks/*/task.toml` and `.sound` markers on the VM;
- the main candidate index `sourcer/index/candidates.sqlite`;
- the stacking selection outputs `pipelines/stacking/out/` (screener, H4 rank, H3b pairs, reader records, batch files).

## Summary

The report is half right. Its count of what the breakers look like holds up. Its explanation of why does not
quite.

Three causes were proposed:
1. not enough sources in the other patterns;
2. the patterns are weak (easily solved);
3. the patterns are strong but our sources for them are weak.

**Verdict:**
- **#1 is the main cause.**
- **#3 is a partial cause.**
- **#2 has no evidence behind it.**
- **Two causes were not on the list:** gate-passed builds never trialled, and path traversal over-built.

## What the report gets right

- 11 of its 18 breakers are A01 (Broken Access Control).
- Its per-pattern candidate counts match the index. For example: deserialization 36, SQL 54, ReDoS 51, XXE 9.

## Two claims are off

**1. "A01 is 51% of builds but only 31% of the pool."**
- The 31% uses a different counting rule from the builds figure.
- It takes each advisory's highest-scoring category (`c_class`). A01 scores zero, so A01 loses every tie.
- Counted the same way as the builds, the pool is 34% A01 by first CWE, or 39% if any CWE counts.
- 52% of trialled tasks are A01. That is a mild skew, not a large one.

**2. "The concentration comes from what we choose to build."**
- Mostly not.
- I followed each pattern through every stage: candidate pool, screener, H4 ranking, reader, chosen batch, trial.
  Each pattern's share stays roughly the same from stage to stage.
- The rarer patterns are each only 1–3% of the pool, so they got 0–4 trials each.

## Q1: Do we have breakers in the other patterns?

**Yes.**
- The ledger now has 50 tasks where both models failed. These are pending audit and fairness review, so not all are
  confirmed breakers.
- 23 of them are outside A01: A05 10, A07 4, unmapped (DoS and similar) 3, A06 2, A08 2, A09 1, A10 1.

**The patterns the report calls "no breaker yet":**

| Pattern | What happened |
|---|---|
| SQL injection | hypequery: both models failed, but its fairness review says NOT READY. mongoose: one model failed. 2 of 2 tried failed at least one model. |
| Request smuggling | h2-s2: both models failed (in repair) |
| Signature checks | oauth-s2: one model failed (1 of 4 tried) |
| Template injection | orval-ds (labelled CWE-94): one model failed |
| Deserialization, ReDoS, race, XXE | barely tested: 0, 0, 1 and 2 trials. Both XXE runs are ungraded because the model looked the fix up online. |

**Rare patterns are not weaker.** Taken together, they produce both-model failures at the same rate as the big ones:

| Group | Graded tasks | Both models failed |
|---|---|---|
| The rarer patterns | 41 | 12 (29%) |
| The 8 big patterns | 149 | 38 (26%) |

The samples are small.

## Q2: Do we have enough sources for them?

**In the current pool (advisories published since 2026-06-01), no.**

- **Too few candidates:** XXE 9, template 15, race 30, deserialization 36, smuggling 43, crypto 45.
- **Most do not fit our recipe.** The screener judges most of these candidates as single-site fixes with no "missed
  another place" route:
  - every XXE candidate scores 0 such routes and ranks below 500;
  - the best race-condition candidate ranks 239;
  - only one signature candidate is in the top 100.
- **ReDoS is excluded by rule.** The screener skips DoS-only CWEs, so 51 ReDoS candidates became 2 screened.

**Older advisories have far more:**

| Pattern | Older advisories |
|---|---|
| XXE | 215 |
| Deserialization | 374 |
| Race | 169 |
| Crypto | 346 |
| Signature | 427 |
| ReDoS | 213 |

## Diagnosis

1. **Not enough sources:** yes, this is the main cause.
2. **Weak patterns:** no evidence.
3. **Strong patterns, weak sources:** partly.
   - In-window advisories in these patterns are mostly one-line fixes that our recipe cannot use.
   - Well-known old ones (XXE in Spring or Lucene) get looked up online.
4. **Built but never trialled** (not on the list):
   - 71 tasks passed the gate and were never trialled. 37 of them are outside A01: SQL 4, signature 3,
     secrets-in-logs 3, deserialization 2, plus crypto, header injection and timing.
   - Most are from the sibling2 batch. Its guide says it "stops at the gate", because no trial launcher exists for it.
5. **Path traversal is over-built** (not on the list). It is our most-trialled pattern (43 tasks) and has the lowest
   yield (5 both-model failures, 12%).

## Remediation steps

1. **Trial the 71 that are already built.** This is the cheapest step, because nothing needs building.
   - It needs a trial launcher driven by a slug list for sibling2.
   - These passed the gate on 2026-10-24. The fingerprint check refuses any whose files changed since.
   - **Started 2026-10-27.**
2. **Set per-pattern quotas when choosing a batch.**
   - Today the batch is the top-N by score.
   - Cap path traversal and access control, and reserve slots for the rarer patterns.
   - Some already rank high: hypequery #8, Jenkins deserialization #29, psr7 #30, orval #31.
   - **Next.** This runs as a separate experiment in `diversity_population/`.
3. **Widen the pool one pattern at a time.**
   - Run diffs and the screener on older advisories for the target CWEs only (about 2,000 entries rather than 15,000).
   - Score the new sources (sources2) for the same CWEs.
   - Allow ReDoS and algorithmic DoS back in. commonmark showed that timing tests work.
4. **Tell the screener where "another place" is for each pattern.** Without this, the screener scores these patterns
   as single-site and drops them.

   | Pattern | Where the other places are |
   |---|---|
   | XXE | every parser factory |
   | Deserialization | every entry point and format |
   | Signatures | every algorithm and key source |
   | Crypto | every mode and configuration |
   | Smuggling | the two parsers that must agree |

5. **Record the pattern in the ledger.** Track yield per pattern, and stop building a pattern once its yield falls.

## Not checked

- The report's claim that 9 of the 18 breakers rest on advisories published before 2026-06-01.
- The report's trap-shape labels (S1–S9).

**Analysis scripts:**
`/private/tmp/claude-501/-Users-dev-terminal-bench/b70882b1-f2eb-4f1e-a8fe-bd7ed8aef484/scratchpad/div/`
(`outcomes.py`, `funnel.py`, `pool_rank.py`).
