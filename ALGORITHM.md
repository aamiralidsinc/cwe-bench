# CWE-Bench task-generation algorithm

Goal: produce 100–200 Harbor-format security-fix tasks where every accepted task
is failed on 3 of 3 runs by **both** DeepSeek V4.1 Flash (max) and
Xiaomi MiMo-V2.6-Pro, with the failure attributable to model capability, not a
task defect. This document records the pipeline, the three task-shape strategies
(branches), the scoring model, and the learning loop.

**Fallback policy.** The pipeline below is the primary path. When it cannot meet the
project's task count, quality or delivery needs, pursue the approaches in
[fallbacks/FALLBACKS.md](fallbacks/FALLBACKS.md). Fallback candidates still pass the same gate,
fairness checks, trials and audits; non-advisory investigations use explicit briefs rather than
fabricated advisory records in the OSV sourcer.

## Pipeline (shared by all branches)

```
sourcer ──► screener/scoring ──► trap calibration ──► builder ──► gate ──► trial (early-abort) ──► verdict
   │             │                     │                 │          │              │
 OSV dumps   weights.json      trap_tally.tsv       BUILDER.md   gate.py        trial.py
 + index     (re-scorable)     (per shape × model)  + templates  (scripted)     (sequential)
```

**Trap calibration (added 2026-10-16, after round 1).** We do not guess which injected
flaws beat the models; we measure it. Before building full tasks from a trap shape:
1. Take 2 host repos and inject ONE trap of a candidate shape on its own (one small task per
   trap, same builder rules and gate as a full task, including a passing blind Opus fix, which
   proves the trap is fair and findable).
2. Run each target model ONCE per single-trap task, offline.
3. Record each outcome in `research/trap_tally.tsv` (shape, host, model, run, caught/missed,
   minutes, audit verdict). The tally is cumulative: every later full-task run that reaches a
   trap adds a row too.
4. Build full tasks only from shapes that each target model misses at a useful rate, and stack
   shapes of DIFFERENT kinds (models that accept a concept fix all its routes together).
   Retire shapes both models keep catching.

Shapes caught by both models in every round-1 run, not worth calibrating: encoding variants,
extra verbs/operations, protocol siblings, the other role or direction, anything the
instruction names. Shapes to calibrate first (round-1 hits, n = 1–6 each): feature-absent
sibling not named (DeepSeek 6/6, MiMo 0/2), linked visible value (over-broad fixes), merged
or defaults route to the same sink, check that must precede an adjustment of the attacker's
value, strict/lenient parser mismatch, fail-open fallback when the authority returns nothing,
symptom-far-from-cause (the fix belongs in a shared layer, not where the symptom shows), and
**data producer off the check's path** (below). Sources:
`research/round1-analysis/B-failure-modes.md`; Hadi's report (2026-10-15).

**Data producer off the check's path (Hadi, 2026-10-15; strongest single-model result so
far).** The fix needs two changes: the CHECK the report points at, and the DATA PRODUCER the
check depends on (schema, serializer, parser, loader, constructor) in another file or package,
which the check does not call: the data reaches the check on a separate path (e.g. saved and
reloaded). DeepSeek fixed the check every time and missed the producer in 8/8 runs (3/3 on the
real, unmodified MCP TypeScript SDK, GHSA-6qxp-vccf-f47h: zod schemas strip the issuer, so a
reloaded credential passes the issuer check). Controls on the same snapshot: check-only bug
solved 1/1; one report sentence pointing at the second path solved 3/3; removing misleading
"backward compatible" comments still failed. It follows calls INTO the check but never asks
where the check's data comes from, keeps the fail-open branch ("no issuer, allow"), and stops
when the repo's own tests pass. MiMo SOLVED Hadi's task (Hadi, 2026-10-16), so this shape is DeepSeek-only so far, like
the feature-absent sibling. Not yet confirmed: a producer the check calls directly (Semaphore UI,
pending). Shape is rare: ~5 of ~45 multi-file fixes Hadi read.
Build rules for it: the report describes impact through the check's path only and never names
the producer; avoid fixes where the check cannot compile without the producer change (the model
is forced to find it); hidden tests must not need a field or function name the model would
have to guess. Task and runs: `Hadi/mcp-ts-sdk-oauth-issuer-confusion_deepseek.zip`.

1. **Sourcer** — mine OSV / GitHub Advisory dumps for real vulns with a CWE, a
   GitHub repo and a source-code fix commit. Writes one row per candidate to a
   persistent index (`sourcer/index/candidates.sqlite`); never re-processes a
   seen advisory. Code: `sourcer/osv_sourcer.py`. Sourcers are tried in order —
   (1) advisory DB, (2) DB entries as seeds for repos not listed, (3) direct
   commit-history scan — moving on when one performs weakly.
2. **Screener / scoring** — assign per-dimension scores to each candidate and
   rank by the weighted model in `weights.json`. Re-scoring runs with no network
   and no model (`remetrics`/`resignal` stages), so new weights re-rank the whole
   pool in seconds. This is the tunable core (see *Scoring model*).
3. **Builder** — turn one candidate into a Harbor task: environment at the
   vulnerable commit (all deps/services installed, offline), a real-entry-point
   exploit plus variants, security tests (fail→pass) and functional tests
   (pass→pass), the oracle fix, and the wrong-fix check patches. Brief:
   `builder/BUILDER.md`. Driven by a sub-agent (DeepSeek in production, Opus in
   development). **Run sequentially**: one heavy build at a time on a single
   machine (4 concurrent Docker builds thrash a 6-CPU/10 GB host).
4. **Gate** — `builder/gate.py`, fully scripted, no model. static (files,
   metadata, leak check) → nop (vulnerable code: security tests fail, functional
   pass) → oracle (fix scores 1.0 twice, identically) → patches (a shallow
   PoC-only fix still fails a security test; a feature-removal fix breaks a
   functional test; an independently-written correct fix still scores 1.0 — this
   last check proves the tests aren't bound to the upstream patch's shape). A
   task is "built" only when the gate prints PASSED.
5. **Trial** — `build/trial.py`, **sequential early-abort**: run one attempt at a
   time, DeepSeek first then MiMo; the instant any run scores 1.0 the task is
   rejected and all remaining runs are skipped (a solved task can't reach
   0-of-3, so further runs are wasted tokens). Accept only if every run fails on
   both models.

State lives in `build/queue.json` (priority queue + verdicts); `build/status.py`
prints a one-screen status from the filesystem.

## The three branches (task-shape strategies)

All three share the pipeline above; they differ only in what the builder
produces. Each candidate/ task carries a `track` field so one index serves all.

### Branch A — mined-only (baseline)
The task is the real vuln as mined: repo at the vulnerable commit + a report; the
oracle is the upstream fix. **Empirically weak (2026-10-14): all 6 top-ranked
mined-only tasks were solved by both models**, because the complete fix is
derivable from the vulnerable code. Kept only as a baseline/control, not a
production source of breakers.

### Branch B — injected siblings
Start from a mined vuln, then **plant one or more same-class sibling flaws on
reachable paths the upstream fix never covered**, placed where such a flaw would
naturally live. The report describes only the observed symptom; applying the
known upstream fix is not enough. This is how Collinear's CWE-bench is built.
- Advantage: the planted bug is novel, so it is **immune to memorization**.
- Risk: must stay realistic and reachable, or it drifts into "contrived /
  unreachable" (out of scope). The gate's variant tests guard reachability.
- Screened by the `injectability` dimension: how many plausible siblings a
  subject supports without looking planted.
- Validation design: on a high-injectability subject, build **with and without**
  siblings (A/B) and trial both, to isolate the siblings' effect.

### Branch C — stacking (real co-present vulns)
Find a repo with many historical security advisories and pick a commit where
several are **simultaneously open** — each was already present (latent) at that
commit, not introduced by a later regression. The streak ends at the commit where
a desired bug was first introduced. One checkout then contains a diversified set
of **real** vulnerabilities; the task requires fixing all of them.
- Advantage: all bugs are real — **no realism risk, no "looks planted" risk**.
  Subsumes the "diversified injection" idea using real bugs.
- Trade-off: each stacked vuln still needs its own exploit + tests (N× build
  cost); the task is hard and may need partial credit; public CVEs carry some
  **memorization** risk (mitigated because trials are offline, so only pure
  recall leaks — no lookup).
- Supply (measured from 48,740 OSV advisories, 2026-10-14): co-presence is
  abundant, not rare — ~1,326 packages have ≥5 co-present CWE vulns and 562 have
  ≥10. Giants (tensorflow, magento, moodle, jenkins) won't build offline; the
  useful zone is the ~1,300 **mid-size** repos with 5–15 co-present vulns.
- Screened by a stacking screener ranking repos on co-presence count × offline
  buildability × favoured-class mix, preferring mid-size over giants.

B and C are complementary: B is unmemorizable but must look real; C is fully real
but memorizable. Run both.

## Scoring model (`sourcer/weights.json`, v3 since 2026-10-16)

Additive points per signal; `score` uses computed signals only (comparable across the pool),
`score_read` replaces proxies with a reader's judgement. Signals:

| # | Signal | Scored from |
|---|---|---|
| S1 | same trust decision needed at several sites | fix diff (same new check at N sites); judged |
| S2 | cause in another place than the symptom (localisation) | advisory wording (weak proxy); judged; computed version planned, see below |
| S3 | a defence existed and did not work | advisory wording + rewritten condition; judged |
| S4 | earlier fix bypassed / repeated advisories | advisory text, sibling advisories |
| S5 | weakness class (OWASP 2025 category + per-CWE evidence) | CWE ids |
| S6 | fix size and spread | fix diff |
| S7 | an over-broad fix breaks legitimate, tested use | judged |
| S8 | undisclosed siblings / alternate routes the advisory and fix do not name | vulnerable tree search (`siblings` stage); judged |
| LOW | single obvious sink, one-site guard, compact fix in a small repo | fix diff |

v3 is fitted on round-1 outcomes (6 mined bases: ρ −0.06 under v2 → +0.76; in-sample, so a
hypothesis to re-check in round 2): S8 added and weighted highest among judged signals, S7
raised, S6 and the wording-only S2/S3/S4 proxies lowered, CWE-287 out of "saturated", CWE-347
out of "DeepSeek weak spot". Evidence: `research/round1-analysis/A-screener-validity.md`.

**S2 (computed, added 2026-10-16).** Localisation is the most consistent failure cause in the
literature and appears in round-1 defects (argo: symptom in the pod, cause in the defaults
merge; asyncssh: symptom a hang in the send loop, cause at channel open) and in Hadi's data
producer result. The wording proxy (+1) fires on easy and hard tasks alike, so S2 gets two
computed parts:
- **S2a named-location disparity** (from `research/owasp_top10_findings.md` §7): locations the
  advisory names (functions, files, endpoints, commands) vs files and functions the fix changes:
  +3 when the fix touches none of them, −1 when it lands exactly on them, 0 when none is named.
  Offline, from the dumps and cached patches.
- **S2b data producer off the check's path** (Hadi): the fix changes a check-role site AND a
  producer-role site (schema, serializer, parser, loader, decoder, constructor, model) in a
  different file or package. From the diff: role pair present. From the vulnerable tree (the
  `siblings` stage): the check does not reach the producer through calls, which is the case that
  beat DeepSeek 8/8.
Both carry 0 points until validated on the round-1 tasks and Hadi's MCP task (where symptom
and fix locations are known); then their points are set from that validation.

Ranking in three stages: (1) computed score over the whole pool (offline, about a minute);
(2) the `siblings` search over the vulnerable tree for the top ~150, adding computed S8;
(3) readers judge the top ~30 (S1–S3, S7, S8, trap labels) and write an injection plan
naming which calibrated trap shapes the code supports.

## Learning loop

After each batch, for every trialed task record the predicted score beside the
actual outcome (rejected / accepted, which model+run solved it). Raise weights on
dimensions that separated breakers from non-breakers, drop the ones that didn't,
add a dimension when a failure reveals one the schema missed, then re-score the
whole pool so the next batch is ranked under the improved rule.

**Status (2026-10-16, end of round 1): 0 breakers; 36 pairs solved, 1 failed
(jackson-databind-sib / DeepSeek 0/6), 1 open.** Mined-only and stacking tasks were solved
offline (29 of 30 pairs); every hard outcome came from what we built into a task (undisclosed
siblings, traps), not from the advisory chosen. Round 2 is therefore injection-first: mined and
stacked candidates serve as hosts, the screener ranks hosts by room for traps (S8, S7, trap
labels), and trap calibration decides which shapes to build. Two learning signals now feed
back: screener features vs outcome (weights) and trap shape vs outcome (`trap_tally.tsv`).

## Capacity & sequencing

- One machine ≈ 2–3 concurrent heavy builds, not 4. Build sequentially until the
  extra machines / cloud Linux server are available; then the same queue spreads
  across them unchanged (set per-machine worker caps).
- Gates and trials need no Anthropic account (gate = nop/oracle, trials = the
  DeepSeek/MiMo keys); only builder sub-agents consume the Opus account.

## Open questions for the client
- Internet during trials: CWE-bench runs the agent offline; our earlier
  assessment allowed internet. (Asked; pending.) We build offline either way.
- Partial-credit definition under their harness (matters for stacking tasks).
- Acceptable fidelity when a repo's real build/test harness won't run offline
  (we substitute standalone tests / sibling jars in some tasks).
