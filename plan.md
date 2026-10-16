# CWE-Bench: status and plan

Last updated: 2026-10-16

**Goal:** 100–200 Harbor security-fix tasks where **both** DeepSeek V4.1 Flash and Xiaomi
MiMo-V2.6-Pro fail all 3 attempts (pass@3 = 0), and the failure comes from the model, not from
a faulty task. Every verdict is per (task, model) pair.

Related documents:
- [ALGORITHM.md](ALGORITHM.md): the pipeline and strategy;
- [RESULTS.md](RESULTS.md): per-task results;
- [research/round1-analysis/](research/round1-analysis/): what round 1 taught us.

---

## 1. Where we stand

| | |
|---|---|
| Tasks built and trialled | 19 (7 mined, 8 stacking, 4 injected-sibling) |
| (task, model) pairs | 38: **36 solved, 1 failed, 1 open** |
| Breakers (both models fail 3/3) | **0** |
| One-model failure | jackson-databind-sib / DeepSeek, 0/6, every run audited as genuine |
| Open pair | asyncssh / DeepSeek: its only offline solve failed a test added in today's repair (independently judged fair); fresh runs wait for a go-ahead |
| Trial setting | offline (model API only, web tools off), 2 h limit, 3 h re-run after a timeout |

Every graded run is audited by an Opus 5.5 sub-agent before it counts. The ledger
(`build/audit/ledger.md`) is the single source of truth.

---

## 2. What we have done

**Round 1: build and trial (to 2026-10-15)**
- Screened 37,416 OSV advisories down to 1,462 candidates, shortlisted 20 mined and 20
  stacking candidates, and built 19 tasks. Every task passed the gate: the vulnerable code fails
  the security tests, the reference fix passes, and wrong fixes are caught.
- Ran 186 trials, about 109 agent-hours.

**Making the results trustworthy (2026-10-15 to 10-16)**
- **Post-run audit:** every graded run is now checked by a sub-agent for test faults, tampering,
  lookups and grading timing before it counts. This found that two reported MiMo failures were
  test faults (since corrected and communicated), and that one MiMo "solve" was a false solve
  that refused every request.
- **Offline trials, like CWE-bench:** runs that looked up the upstream fix online solved 43 of 44.
  Every open pair was re-run offline.
- **Test repair on all 16 tasks the audits flagged:** each change follows only from what the
  instruction states. About 55 new wrong-fix checks prove the tests catch what they should, and
  saved solves were regraded. One pair reopened (asyncssh / DeepSeek). The rest held.

**Research and analysis**
- Taxonomies checked against repair benchmarks and our runs: CWE Top 25, OWASP Top 10:2025, the
  MITRE CWE hierarchy, CVSS / EPSS / KEV, CAPEC / ATT&CK / STRIDE. Category labels predict little.
- Round-1 analysis (three reports):
  - **Screener validity:** the literature-only v2 weights did not rank difficulty (ρ −0.06).
  - **Failure modes:** models always find the vulnerable code. They fail by judging wrongly about
    sites the report does not mention.
  - **Pipeline lessons:** about half of all trial time was lost to our own faults or setting changes.
- Hadi's finding (2026-10-15): DeepSeek fixes the check but misses the data producer that feeds
  it when that producer sits on a separate path (8/8 runs). MiMo solved the same task.

**Pipeline changes already made**
- Screener weights v3 (`sourcer/weights.json`):
  - added S8, undisclosed siblings, the strongest signal;
  - raised S7, an over-broad fix breaks legitimate use;
  - lowered fix-size and wording-only signals;
  - corrected two CWE weights.
- Computed S2 built as labels, 0 points until validated:
  - S2a, fix away from the locations the advisory names: does not measure what we hoped;
  - S2b, a check plus a data producer in another file: fires on Hadi's case, 5.5% of the pool.
- **Trap calibration** added as a pipeline stage. A per-shape, per-model tally is kept in
  `research/trap_tally.tsv`.
- Harness changes:
  - post-run audit with audits carried over to unchanged regrades;
  - a shared Docker slot cap, set by you (now 2);
  - a repair hold so the queue never runs a task whose tests are being edited.

---

## 3. What we learned

1. **Difficulty comes from what we build into a task, not from which advisory we pick.**
   Mined-only and stacking tasks were solved offline (29 of 30 pairs).
2. **Models fix what the report points at.** They miss:
   - a sibling where the protection is absent and unmentioned;
   - a second route to the same sink (defaults or merged config);
   - a check that must come before an adjustment of the attacker's value;
   - a parser mismatch;
   - a fail-open fallback;
   - the data producer behind a check.
3. **Models always catch:** encoding variants, extra verbs, extra protocols, the other role or
   direction, and anything the instruction names.
4. **Only two shapes beat a model every time, and both are DeepSeek-only:**
   - a feature-absent sibling (DeepSeek 6/6, MiMo 0/2);
   - a data producer off the check's path (DeepSeek 8/8, MiMo solved).

   **No shape is known to beat MiMo reliably**, so MiMo is the bottleneck for a both-model
   breaker.
5. **A both-model breaker likely needs several traps of different shapes stacked.** Four
   independent traps, each missed half the time, give about an 80% chance of failing 3/3 for one
   model. More routes of one shape do not help.

---

## 4. Next steps (in order)

Each step ends with a review before the next starts.

| # | Step | What it produces | Status |
|---|---|---|---|
| 1 | **Sibling search**: download the vulnerable source and compute S8, the "check never calls the producer" part of S2b, and a code-based S2. Top 150 first (85 repos, under 1 h), then the remaining ~1,300 in the background (3–4 h). | Re-ranked pool | awaiting go-ahead |
| 2 | **Reading**: reader agents judge the top ~30 and write an injection plan per candidate (which trap shapes the code supports, with file and line). | Top 20 with score breakdown and injection plans, **shown to you before any build** | after 1 |
| 3 | **Harden the pipeline before building** (round-1 lessons, in order of impact): see §5 | Stricter builder brief, gate and templates | partly done |
| 4 | **Trap calibration, MiMo first**: one small single-trap task per shape on 2 hosts; run each model once offline; record in the tally. Priority is finding shapes MiMo misses. | Measured miss rate per shape and model | after 2–3 |
| 5 | **Build the round-2 batch** (the next 6+6), injection-first: each task stacks one feature-absent sibling plus 3 or more traps of different calibrated shapes, with nothing named in the instruction. | New tasks through the stricter gate | after 4 |
| 6 | **Trials**: one pilot run per model first and stop at the first solve; then the full 3 runs; audit every run before it counts. | Verdicts per pair | after 5 |
| 7 | **Learning loop**: compare screener scores and trap shapes with outcomes; update weights and the tally; re-rank. | v4 weights, updated tally | after 6 |

Side items (whenever useful, each needs a go-ahead):
- asyncssh / DeepSeek: 2 fresh offline runs to settle the open pair.
- Optional hardening flagged by audits: async-http-client's malformed-cookie test should check
  that a request is actually sent; a UTF-7 target case for cloudreve.

---

## 5. Pipeline hardening checklist (step 3)

| Change | Prevents | Status |
|---|---|---|
| Post-run audit before any run counts | false failures and false solves | done |
| Offline trials with web tools disabled | upstream fix lookup | done per task; not yet in the task template or gate check |
| Repair hold and shared slot cap | runs on half-edited tests; machine overload | done |
| `strict_gate` on by default, with hardening and blind pass patches required | tests bound to the upstream fix's shape | not done |
| Required standard wrong-fix patches: refuse-all, crash counted as a refusal, wrong resource, one role only, reads only, check after an adjustment | lenient tests found only after trials | not done |
| Independent fairness and leniency review of the tests before trials | test faults found after trials | not done (done ad hoc today) |
| Oracle run 5 times, some under load | flaky tests (trigger-dev, cloudreve) | not done |
| Gate check for upstream regression tests shipped in the image; blind-agent leak check | leaked answers (webob, jackson-sib7) | not done |
| Agent kill in the template `test.sh` | agent editing during grading | done per task; not in the template |
| Always harvest final code (source first, no truncation) | runs that cannot be regraded (137 of 186) | partly done |
| Freeze trial settings for a whole round; record cost per stage | voided runs; unknown build and audit cost | not done |
| Instruction rules: never name a sibling; no wording that suggests a limit; state any interface a test needs; use "works exactly as today" preservation clauses | wording-induced outcomes (jackson-sib7, cloudreve, rclone) | written in the analysis; not yet in BUILDER.md |
| Disk budget: remove regrade images when a task's repair ends; never prune the build cache | disk full (twice on 10-16) | agreed; not automated |

---

## 6. Blockers and risks

- **Compute.** Builds and gates are heavy on CPU, RAM and disk. The Docker VM has 8 CPUs, 12 GB
  RAM and a 79 GB disk; the disk filled twice on 10-16. Work runs 2 at a time. A larger Linux
  machine (16+ cores, 64 GB RAM, 200 GB disk) would allow about 4× the parallelism.
- **MiMo.** No trap shape is yet known to beat it reliably. Calibration targets this first.
- **Small samples.** The v3 weights are fitted on 6 bases and the trap rates on 1–8 runs each.
  Treat both as hypotheses until round 2 confirms them.
