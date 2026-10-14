# CWE-Bench task-generation algorithm

Goal: produce 100–200 Harbor-format security-fix tasks where every accepted task
is failed on 3 of 3 runs by **both** DeepSeek V4.1 Flash (max) and
Xiaomi MiMo-V2.6-Pro, with the failure attributable to model capability, not a
task defect. This document records the pipeline, the three task-shape strategies
(branches), the scoring model, and the learning loop.

## Pipeline (shared by all branches)

```
sourcer ──► screener/scoring ──► builder ──► gate ──► trial (early-abort) ──► verdict
   │             │                   │          │              │
 OSV dumps   weights.json      BUILDER.md    gate.py        trial.py
 + index     (re-scorable)     + templates   (scripted)     (sequential)
```

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

## Scoring model (`weights.json`)

`score = ( Σ value_i · weight_i  −  memorization · w_mem ) · Π (validity_j / 10)`

- **Value dimensions** (additive) measure how hard the bug is for the models.
- **Validity multipliers** (0–10 → 0–1, multiplied in) gate the score: an
  unbuildable or unreachable candidate scores ~0 no matter how hard the bug is.
- **Memorization** is a subtractive penalty (recent + obscure = low penalty).

Top weights, from research + the 2026-10-14 results: `injectability` and
`wrong_fix_trap` dominate, because mined hardness alone (multi-site, size) was
shown not to beat the models. `multi_site` is down-weighted from its original
value. `wrong_fix_trap` is scored 0–10 by how *hidden* the trap is (more hidden =
higher): 10 = the obvious local fix would pass review yet misses the real cause.

See `weights.json` for the exact dimensions, scoring rules and weights.

## Learning loop

After each batch, for every trialed task record the predicted score beside the
actual outcome (rejected / accepted, which model+run solved it). Raise weights on
dimensions that separated breakers from non-breakers, drop the ones that didn't,
add a dimension when a failure reveals one the schema missed, then re-score the
whole pool so the next batch is ranked under the improved rule.

**Calibration status (2026-10-14): 6 negatives, 0 positives — not yet
calibratable.** v1 weights are a research-grounded prior. The injected-sibling
and stacking experiments must produce the first accepted breakers before the loop
can learn the breaker direction from evidence.

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
