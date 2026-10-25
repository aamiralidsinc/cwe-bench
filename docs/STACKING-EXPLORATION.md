# Stacking exploration: definitions, a scoring cube, and open items (2026-10-20)

**Scope.** This file is about **trap stacking**: one task holding several traps, as in
jackson-databind-sib2, the only audited both-model breaker. It is not about Branch C, where several
separate real vulnerabilities share one checkout; `sourcer/stacking_screener.py` covers Branch C.

**Status.** Exploration only. Nothing here is wired into the pipeline yet.

**Related:**
- `BETTER-PATTERNS.md` §1.3a: why stacking worked once;
- `reports/SIBLING-INJECTION-PATTERNS.md`: 93 tasks, 609 traps.

---

## 1. Terms

- **Trap:** one concept a fix can miss, meaning one reason a model might skip it (one `manifest.traps`
  entry). A trap can span **one or several locations** (sites in the code).
- **Trap kind:** the mechanism code (M1-M12, see the report §2), plus the coupled and shape traps.
- **"A single hard trap"** means one hard **concept**, whether it sits at one site or several. It
  does not mean one site fixed differently by several commits. Examples from the near-misses:

  | Task | The single hard trap | Sites |
  |---|---|---|
  | prompty T2 | child-prompt paths read when the prompt runs | 2 (wire projection, dispatch) |
  | siyuan T6 | listings shown to readers | several listing routes |
  | electron-builder-ds T4 | secrets in free-text output | child-command output, publisher errors |

- **Why several sites of one kind count as about one trap:** once a model accepts the concept, it
  fixes every site of it together.
  - sib7: the 5 any-setter routes were closed together, 10/10 for DeepSeek and 3/3 for MiMo.
  - Planted siblings that were more routes of one concept were missed 5 times out of 98.

  Extra sites of an accepted concept add almost nothing. Extra sites matter only when a site is
  hidden enough to be missed **after** the concept is accepted.
- **Why a single hard trap does not make a both-model breaker:**
  - **Three runs.** With a per-run miss chance `p`, failing 3/3 has chance `p³`.
  - **Different models.** The models miss different kinds (§2.3), so one kind rarely beats both.
  - **Every near-miss in the data rested on one trap.** In sib2, every run failed at least two
    independent parts.

---

## 2. Difficulty of a trap

### 2.1 There is no formal definition yet

Until now "hard" and "easy" were judged case by case. Below is a proposal grounded in the data.
Difficulty is **per model**.

### 2.2 Proposed tiers (to be refitted from `research/trap_tally.tsv`)

The rates in the "Data" column count a trap as missed when it was missed in at least one run.
Per-run rates should replace them once the tally is filled.

| Tier | Per-run miss rate (target definition) | Kinds and cases in this tier today | Data |
|---|---|---|---|
| easy | under 10% | M12 spelling/encoding/verb variants; any trap whose surface the report describes; more routes of an accepted concept; planted M1/M2 under surface-describing reports | M12 0 misses; planted siblings 5/98 |
| medium | 10-25% | M1 parallel entry, M2 second implementation, M5 merged/defaults, M10 wrong object (under a general report) | M1 12/99, M2 14/73, M5 2/14, M10 2/11 |
| hard | 25-50% | M4 protection absent, M6 producer off path, M8 shape a check mishandles, M11 coupled value | M4 7/22, M6 5/17; airflow T10; sib2 C1 4/6 |
| xhard | at least 2/3 of a model's runs on that instance | M4 with a strong reason to dismiss; a deep how-type mechanism | sib catch-all DS 6/6; electron-builder-ds T4 DS 9/9; siyuan T6 DS 3/3; sib2 catch-all 6/6 both |

### 2.3 The two models miss different things

| Model | What it misses | Examples |
|---|---|---|
| DeepSeek | a route where the protection is absent and there is a reason to dismiss it | sib catch-all; siyuan T6; electron-builder-ds T4 |
| MiMo | coupled values (it over-hardens) and how-type mechanisms | sib2 C1 and the record id; airflow's over-broad zeros |

A trap's tier must therefore be recorded for each model separately.

### 2.4 Before any trial: predicting the tier

Use the how/where split (`BETTER-PATTERNS.md` §5), plus four questions:
- Is there a reason to dismiss?
- How far is the trap from where the report leads?
- How big is the codebase?
- Does the report describe the trap's surface? If it does, the trap is **easy**, whatever its kind.

---

## 3. The stacking cube: dimensions to score

Every stacking design is scored on these dimensions, for each target model.

| # | Dimension | What it measures | Measured or judged |
|---|---|---|---|
| D1 | **Number of trap kinds** (cardinality) | distinct concepts, each with its own reason to dismiss; several traps of one kind count as 1 | counted |
| D2 | **Difficulty of each trap** | tier (§2), per model; a kind-level prior from the tally | measured (tally), else predicted |
| D3 | **Number of locations per trap** | sites of that trap | counted |
| D4 | **Hiddenness of each location** | how hard that site is to reach once the concept is accepted: distance from the landing point, another package, codebase size, nothing in the report pointing at it | judged |
| D5 | **Hiddenness of the trap itself** | how hard the concept is to see or accept here: strength of the reason to dismiss, how-type depth | judged |

**Decision (2026-10-21): score D1-D3 now.** D4 and D5, the two judged hiddenness dimensions, are
recorded but not scored until there is data to calibrate them.

**D2 vs D5: keep both for now.**
- D2 is a property of the **kind**, measured across tasks.
- D5 is a property of **this instance**. The same kind (M4) is xhard in sib, with "upstream doesn't
  support it", and easy in jackson-databind-readonly, where the protection is documented with no
  exceptions.
- D5 adjusts D2 for the instance. If the data later shows D5 adds nothing beyond D2, merge them.

**Coupled traps** are a trap kind in D1 (M11). They count toward the MiMo side.

---

## 4. Combining the dimensions into a score

**Option A, additive** (a weighted sum of D1-D5). This is simple, but it rewards piling up easy
traps or easy sites. That is exactly what the pipeline did, and those tasks were solved. Not
recommended.

**Option B, multiplicative** (a product of factors). This punishes any zero factor. But multiplying
counts (D1, D3) by tiers gives a number with no clear meaning.

**Option C, probabilistic (recommended).** Turn each trap into a per-run miss probability per
model, then compute the chance of a breaker:

```
p(t, m)        = base miss prob of trap t's tier for model m   (D2)
                 x hiddenness factor of t                       (D5)
p_site(t, m)   = extra chance that a hidden site is missed after the concept is accepted (D3, D4)
p_concept(t,m) = 1 - (1 - p(t,m)) x (1 - p_site(t,m))           (one trap, however many sites)
P_solve(m)     = product over distinct concepts c of (1 - p_concept(c, m))   (D1)
P_fail3(m)     = (1 - P_solve(m))^3                             (3 attempts)
Score          = P_fail3(DeepSeek) x P_fail3(MiMo)               (both must fail)
```

What option C captures:
- **Redundancy:** more independent hard concepts drive `P_solve` towards 0.
- **Easy piles count for nothing:** several sites of one concept stay one factor.
- **Complementarity:** a design must be hard for both models, because the score is a product.

**Illustration** (made-up probabilities, only to show the mechanics):

| Design | DeepSeek | MiMo | Score |
|---|---|---|---|
| sib2-like: catch-all, record id, coupled value, merge | `P_solve ≈ 0.01`, `P_fail3 ≈ 0.97` | `P_solve ≈ 0.04`, `P_fail3 ≈ 0.89` | ≈ 0.86 |
| prompty-like: one hard trap (T2) | p ≈ 0.5 → `P_fail3 ≈ 0.13` | p ≈ 0.9 → `P_fail3 ≈ 0.73` | ≈ 0.09 |

**Caveat.** Option C assumes the traps are independent. In practice a careful run tends to catch
everything, so the misses are positively correlated and the score is an upper bound. Calibrate it
against known outcomes (§6).

---

## 5. Weights file: `stacking/stacking_weights.json` (created 2026-10-22, v1)

- **Kept separate from `sourcer/weights.json`.** That file scores hosts and advisories for the other
  task types, and must not change for this.
- **Fields it needs:**
  - `version`, `updated`;
  - `scope: "trap-stacking"`, to avoid confusion with Branch C;
  - the combine method (`"probabilistic"`);
  - per-model base miss probability for each tier (D2);
  - per-model kind priors by mechanism code, with their source (tally rows);
  - the hiddenness factors for D5 and the site factor for D3/D4, as small judged scales such as
    0-3;
  - the correlation rule: sites of one concept collapse into one factor;
  - the number of attempts (3).
- **Learning loop:** refit the base probabilities and kind priors from the tally after every trial
  batch, bump the version, and re-score the designs.

---

## 6. How to calibrate

1. **Fill `research/trap_tally.tsv` per run and per trap.** Map each graded run's failing security
   tests (VM `verifier/*/results.xml`) to `manifest.traps` ids. This was done by hand for the
   2026-10-20 analysis; make it a script.
2. **Calibration set with known outcomes:**
   - jackson-databind-sib2 (breaker);
   - jackson-databind-sib (DeepSeek only);
   - the near-misses: prompty, electron-builder (both), siyuan, hermes, airflow;
   - solved controls: readonly, marshmallow, better-auth, and the 30 solved pilot tasks.
3. **Acceptance check:** the score must rank sib2 first, the single-model near-misses next, and the
   solved tasks last. If it does not, adjust the factors before using the score for new designs.

---

## 7. Items from the 2026-10-20 analysis that are in no plan yet (consider later)

1. **MiMo attention-dilution hypothesis.** In sib2, MiMo left the catch-all open in all 3 runs,
   though it fixed the same route in sib, where there were fewer traps. Test it: give MiMo the sib2
   build with the record-id and merge traps removed, and see whether it fixes the catch-all again.
2. **No single trap may carry a task.** Beyond the gate's per-trap wrong-fix patches, check this
   after trials: a task whose failed runs all miss the same one trap is a single-point task. Mark it
   for hardening, not as a breaker lead.
3. **Coupled traps are nearly absent from the pipeline builds.** Only the jackson family, russh-sib
   and nhost have two or more. Consider requiring one coupled trap per hidden route. The builder now
   counts a coupled value as a how-type lever, but does not require one per route.
4. **Design for both models explicitly.** Require at least one DeepSeek-type trap (protection
   absent, plus a reason to dismiss) and one MiMo-type trap (a coupled value or a how-type
   mechanism) in every stacked design. This is not in the builder yet.
5. **Upgrade the near-misses by adding the missing complementary trap:**

   | Task | Has | Add |
   |---|---|---|
   | prompty | a trap MiMo misses | a DeepSeek-type trap |
   | siyuan-ds | a trap DeepSeek misses | a MiMo-type trap |
   | electron-builder-credential-leakage | a trap MiMo misses | a DeepSeek-type trap |
   | electron-builder-ds | — | a second independent hard trap, so T4 stops carrying the task alone |
   | hermes-agent-ds | a trap MiMo misses | a DeepSeek-type trap |
   | airflow-info-exposure-inj | a trap MiMo misses | a DeepSeek-type trap |

   Fix the known test problems first (prompty's wording; the over-broad failure behind airflow's
   MiMo zeros).
6. **Ablate sib2** (also `BETTER-PATTERNS.md` §1.4): remove one ingredient at a time (coupled
   values, the absent-protection route, the how-type route), or name the routes, and re-run.
7. **Test-artifact detector before counting a near-miss.** When both models fail the same security
   tests in every run, open one patch and the test output before counting it. Two such cases were
   artifacts (vitest-api-fs-authz-inj, backstage-ds).
8. **Per-model tiers in the tally.** Record difficulty per model, not just per kind, since the
   models miss different things (§2.3).

---

## 8. Fix-history patterns: how the stacked bugs and their fixes sit in the project's history (2026-10-21)

The cube in §3 describes what a task contains. This section describes where the stacked bugs come
from: which commits introduced them and which commits fixed them. History matters for two reasons:
- what the models may remember from training;
- whether upstream's own fix is a correct answer to the task.

### 8.1 The patterns

| Id | Pattern | What happened upstream | Expectation |
|---|---|---|---|
| **H1** | **Single source, single fix** | N bugs present at commit X; one later commit fixes all N | weak: recalling that one commit fixes everything, and N bugs fixed together are often one concept |
| **H2** | **Single source, staggered fixes** | N bugs present at X, fixed over several later commits (for example 1, then 2, then 1) | weaker than hoped: the round-1 Branch C tasks were solved. Small sample (8 tasks), and their reports named every flaw, so H2 has not yet been tested under the general-rule instruction (`BETTER-PATTERNS.md` §2). Keep it as a category to measure. |
| **H3** | **Fix leads to a follow-up bug** | a fix for the bugs at X leaves or creates further bugs, over one or more commits | promising: a model that recalls upstream's first fix reproduces its mistake, so the recalled fix is a wrong fix |
| H3a | *Regression* | the fix introduced a new bug. **The new bug must come from the code the fix added or changed**, not from elsewhere. | |
| H3b | *Incomplete fix* | the fix closed only part of the bug; a later advisory calls it incomplete or a bypass | |
| H3c | *Masking* | bug B is reachable or visible only once bug A is fixed (for example, A's crash or early exit hides B). Common in H3 chains, where fixing A uncovers the next bug. | a model that fixes A and re-runs its own repro sees it pass and stops. Design note: B's security test must still fail on the pinned code through B's own route, so the gate's nop stage holds. |
| **H4** | **Partial route fix** | one bug with several routes; the next commit fixes only one route | proven: this is our Pattern B. Real uncovered routes were missed 25% of the time vs 5% for planted siblings; jackson-databind-sib2 is built on it. |

**General rule, for every pattern: one shared guard collapses the stack.** If a single guard or one
fix site closes all the stacked bugs, they are one concept and count as one trap (D1 = 1), whatever
their history. Check the reference fix: count its independent edit sites and concepts, not the
advisories or commits.

**Dimensions to score for H3:**
- bugs present at each commit of the chain;
- chain length, meaning over how many commits the problem continues (at least 2; longer is better).

**Record per stacked bug:** the introducing commit, the fixing commit(s), and the link to the other
bugs (fixed together / staggered / regression of / incomplete fix of).

### 8.2 Supply, measured on our OSV dumps (286,684 advisories, 13,518 packages)

| Pattern | Measured | Read |
|---|---|---|
| H1 | 12,927 groups where 2 or more advisories share one fixed version, in 4,023 packages | over-counts: matched at version level, and large release bundles group unrelated bugs. Abundant either way. |
| H2 | 6,329 packages with 2 or more advisories | not counted separately yet |
| H3a | **cannot be measured from advisory metadata** | version-level "B introduced at A's fixed version" gave 27,508 pairs, almost all release coincidences (e.g. Liferay bundles). Only 1,537 advisories carry commit-level ranges, and they gave 0 pairs. H3a needs git-history mining: the SZZ method (blame the lines B's fix changes; is the blamed commit A's fix?). |
| H3b | **455 GHSA advisories in 288 packages** explicitly name an earlier CVE or GHSA as an incomplete fix, a bypass or a regression | a usable pool. The "fix for CVE-…" wording includes some false positives. yamcs, one of our breaker hosts, is in it. |
| H4 | computed today by the screener (O8, uncovered routes) and the scorer's S8 | already in use |

Scripts: `fixhist.py`, `fixhist_git.py` and `fixhist_txt.py` in the session scratchpad (2026-10-21).
Copy them into `sourcer/` if we build on them.

## 9. Does this categorisation add value? (evaluation, 2026-10-21)

**Yes for H3 and H4. Little for the H1 vs H2 distinction.**

**The deciding fact:** the solver sees only the pinned commit. The commit history itself is
invisible to it, so a history pattern can change the outcome only in three ways:
1. through **recall**: what the model remembers of upstream's fix;
2. through **whether upstream's fix is a correct answer**. If it is not, recall works against the
   model;
3. through **concept independence**: whether the stacked bugs are separate concepts (D1).

**How each pattern does on those three:**
- **H4 and H3 (high value).** Both make upstream's own fix a wrong fix: H4 leaves routes open; H3a and
  H3b make the remembered first fix incomplete or harmful. This matches what beat the models so far.
  It is the same principle as the 2026-10-20 yamcs decision: change the tests and the reference so
  that upstream's fix becomes a wrong fix. There is evidence recall is real offline: on
  jackson-databind-sib, DeepSeek reproduced the published fix and stopped. Both patterns are also
  real code with real history, so realism and fairness are easy to argue.
- **H1 vs H2 (low, uncertain value).** The difference is only how upstream split its commits. The
  solver cannot see that, and it shifts recall only a little (one advisory versus several). Its
  likely real effect is D1: bugs fixed in one commit are more often one concept. So record H1/H2 as a
  cheap label. Do not score it until the data shows a difference.

**The risk of over-categorising.** We have 1 confirmed breaker and about 60 trialled tasks. Every new
category splits that data thinner. So:
- keep at most three history labels in scoring for now: H1/H2 as one "co-present" label, H3, H4;
- tie each one to a test (§11).

## 10. Additional patterns identified by the LLM (Claude, 2026-10-21)

Proposed by Claude during the 2026-10-21 analysis, then reviewed by the user. Each carries its status:
- **IN PLAN:** included in the current stacking plan;
- **RECORDED:** kept for later, not in the current plan;
- **MOVED:** turned into a general rule or a sub-pattern elsewhere.

**IN PLAN (user decision, 2026-10-21):**
- **F5. Fixes made by upgrading a dependency.** The instruction must allow an in-repo fix, since the
  solver works offline and cannot upgrade.
- **F7. Masking**, now sub-pattern **H3c** in §8.1.
- **F8. Conflicting fixes:** the natural fix for A breaks a must-keep-working value B relies on. A
  coupled trap across two stacked bugs.

**MOVED:**
- **F9. A shared guard collapses the stack** is now a general rule for every pattern (§8.1).

**RECORDED (not in the current plan):** the remaining items below.

**From the history (sourcing):**
- **F1. Fixes after the models' training cutoff cannot be recalled.** This is the strongest
  protection against memorisation. We record recall risk (O13), but not the fix date against each
  target model's cutoff. Record it, and prefer post-cutoff fixes for H1/H2 tasks.
- **F2. Silent fixes:** bugs fixed upstream with no advisory (inside a refactor or a feature change).
  Recall is low, and they are realistic and fair. Find them with SZZ or a diff review. Routes never
  fixed at all (still in the latest release) have zero recall, but carry the disclosure hold.
- **F3. Fix reverted, then re-landed differently.** It confuses recall: a variant of H3.
- **F4. Backport divergence:** the correct fix on the pinned branch differs from the mainline fix
  the model remembers.
- **F5. Fix by dependency bump** (IN PLAN): upstream fixed it by upgrading a dependency. Offline the solver
  cannot upgrade, so the instruction must allow an in-repo fix (a fairness check).
- **F6. The same bug in forks or vendored copies:** the model may recall another project's fix,
  whose shape does not fit here.

**From how the stacked bugs interact:**
- **F7. Masking** (IN PLAN; moved to H3c in §8.1): bug B is reachable or visible only once bug A is fixed (A's crash hides B). A
  model that checks with its own repro after fixing A stops there. This is natural in H3 chains.
  Design note: B's security test must still fail on the pinned code through its own route.
- **F8. Conflicting fixes** (IN PLAN): the natural fix for A breaks a must-keep-working value B
  relies on. A coupled trap across two stacked bugs.
- **F9. A shared guard collapses the stack** (MOVED to a general rule, §8.1): if one guard closes all stacked bugs, they are one
  concept (D1 = 1). Check the reference fix's independent edit sites.
- **F10. Common origin:** bugs introduced by the same commit (one feature) tend to be one concept;
  bugs from different commits or authors tend to be independent. Use the introducing commits (SZZ) as
  evidence for D1.

**For the experiment itself:**
- **F11. Instruction for several distinct protections.** One general property per protection is
  allowed, but each extra property reveals a concept. Measure that cost against one umbrella
  property.
- **F12. Effort budget.** More stacked bugs mean more time. Timeouts count as failures, but a task
  needing well over about 45 minutes of expert work invites a "too big" objection. Record the
  reference fix size and the blind fix time.
- **F13. Reward.** Any functional failure scores 0, and stacking raises the risk of an over-broad
  fix. In the tally, separate "failed by a miss" from "failed by over-hardening".
- **F14. Correlated misses.** A careful run tends to catch everything, so the independence product in
  §4 overstates. Measure per-run joint misses.
- **F15. Controls.** For each stacked task, run a one-bug control on the same host. That attributes
  the effect to stacking, not to the host.
- **F16. Recall check in the gate.** The patch equal to upstream's fix commit(s) must score below 1.0.
  For H3, so must upstream's first fix. The gate already does part of this ("upstream fix alone").

## 11. Proposed experiment order (not started)

1. **H4 + stacking** (known to work): replicate the sib2 recipe on 2 new hosts (§1.4 of
   `BETTER-PATTERNS.md`).
2. **H3b** (455 linked advisories): build 2 tasks where the pinned commit is before the first fix and
   the task requires the complete fix, so upstream's first fix is a wrong fix.
3. **H3a**: run SZZ over the H3b pool and our clones to find true regressions. Build 2 tasks.
4. **H1 vs H2**: 2 hosts each, under the general-rule instruction. Lowest priority.

**The three IN-PLAN items from §10, folded into these experiments:**
- **H3c masking:** in the H3 tasks (steps 2-3), prefer chains where fixing the first bug uncovers the
  next.
- **F8 conflicting fixes:** in every stacked design, look for a pair where the natural fix for one
  bug breaks a must-keep-working value the other needs, and test that value functionally.
- **F5 dependency-bump fixes:** when screening hosts for all steps, flag advisories that upstream
  fixed by upgrading a dependency. Keep them only if the instruction allows an in-repo fix and the
  gate proves one exists.

Each task gets a one-bug control from the same host (F15).

**Decisions (2026-10-22):**
- **Builder model for Phase 2: DeepSeek V4.1 Flash.**
- **The tooling** is in `cwe-bench/stacking/` (see its README).
- **Fairness:** stacked tasks get `stacking/STACKING-FAIRNESS-ADDENDUM.md`, which covers the coupled,
  shape, fixture, independence, history, contract and decisive-test checks. Each runs offline, both models, 3 runs,
and is scored with D1-D3 plus its history label.
