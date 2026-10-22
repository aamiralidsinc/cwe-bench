# Pattern placement audit: are the sibling-injection patterns in each pipeline stage? (2026-10-21)

**Scope.** The patterns from `reports/SIBLING-INJECTION-PATTERNS.md`, checked against the **live**
prompts on the VM (`~/cwe-bench`, pulled 2026-10-21):
- the trap kinds: far site, uncovered route, injected, shape trap, coupled trap;
- the mechanisms M1-M12;
- the strategy findings: where vs how, reason to dismiss, per-model complement, single-trap carry.

**This is an audit only. No stage file was changed.**

**Stages and the files that drive them:**

| Stage | Files the live pipeline feeds the agent |
|---|---|
| Screener | `SCREENER-PROMPT-v2.md` (writes the screening records); `SELECT-PROMPT.md` (lane selection, LLM scoring over `build/pipeline/pool.jsonl`) |
| Scorer | `sourcer/weights.json` v3. Local repo only. **Not used by the live lanes**: no VM script computes it, and the VM only cites it inside the screener prompts. |
| Builder | `TASK-BUILD-PROMPT-v1.md` (via `build_prepare.py`, into each `BUILD-PROMPT.md`) and `SELFDESIGN-PLAN.md`; `BUILDER.md` for hand builds only |
| Hardening | `HARDENING-PROMPT.md` (`pipeline/run_harden.sh`, `harden_solved.sh`) |
| Upgrade | `UPGRADE-PROMPT.md` (`run_upgrade.sh`): retrofits BETTER-PATTERNS onto already-built tasks |
| Fairness | `FAIRNESS-REVIEW-BRIEF.md` (`run_fairness.sh`); runs **after** the trial |
| Fairfix | the inline prompt in `run_fairfix.sh`, which also reads the fairness brief |

**Key:**
- ✓ explicit and actionable (a rule, a field, or a menu item with guidance);
- ~ mentioned only (a list item or an example, no rule);
- ✗ absent;
- — not needed in this stage.

---

## 1. The matrix

| Pattern | Screener + Select | Scorer (unused) | Builder | Hardening | Upgrade | Fairness | Fairfix |
|---|---|---|---|---|---|---|---|
| Far site, published fix (A) | ✓ O1, O2 kinds; Select ✓ | ~ S1/S6 | ✓ Pattern A | — (the base build has them) | ~ §8 coverage | ✓ general property covers | ✓ |
| Uncovered real route (B) | ✓ O8 + reason; Select ✓ | ✓ S8 (strongest) | ✓ Pattern B + rules | ✓ O8, Part 1 | ✓ §8 | ✓ step 4 + gate a | ✓ never remove it |
| Injected sibling | ✓ O8b; Select ✓ ("extra only") | — | ✓ item 6; Plan says "2-4 siblings" | ✓ O8b | ✓ (one how-type) | ✓ realism | — |
| **Shape trap** | ~ O6 records shapes the fix handles, not shapes a check mishandles; Select ✓ | ✓ label `parser_mismatch` (0 pts) | ~ item 3 is generic "input-shape variants"; how-type text gives one example | ✗ | ✓ (M8 how-type) | **✗** | **✗** |
| **Coupled trap** | ✓ O5; Select ✓ | ✓ S7 + label (0 pts) | ✓ item 4 + test rule | ✓ "coupled behaviour per lever" | ✓ | **✗ no contradiction check** | **✗** |
| M1 parallel entry | ✓ O1/O8; Select ✓ (minor) | ~ | ✓ (as extra) | ✓ O8 | ✓ (as extra) | ✓ layer rule | ✓ |
| M2 second implementation | ✓ O2 kind + lessons-v2; Select ✓ | — | ✓ Pattern A, full rule | ✓ | ~ (covered by §2) | ~ layer rule only | — |
| M3 shared layer | ✓ O2 `lower_level_api`/`wrapper`; Select ✓ | ✓ S2 | ~ listed | ✗ | ✗ | ✓ layer rule | — |
| **M4 protection absent** | **~ O8 does not record absent vs weak** (O12 holds only the opposite flag); Select ✓ | ~ S8 | ✓ how-type + Pattern B | **~ not named** | ✓ | ✓ step 4 | ✓ |
| **M5 merged/defaults** | ✓ O2 kind; Select ~ | ✓ label (0 pts) | ~ listed in Pattern A | **✗** | ✗ | **✗** (state the sink, not the entry) | ✗ |
| M6 producer off path | ✓ O7 + `check_calls`; Select ✓ | ~ S2b (0 pts) | ✓ full rules | ✓ (refers to builder rules) | ✓ | ~ no "no guessed field names" check | — |
| **M7 ordering** | **✗ no field** | ✓ label (0 pts) | ~ one example ("rename after the check") | **✗** | ✗ | ~ only "before vs after setup" when accepting fixes | — |
| M8 parser differential | ~ O6 + lessons-v2; Select ✓ | ✓ label (0 pts) | ~ example | ✗ | ✓ | **✗** (see shape trap) | ✗ |
| M9 fail-open | ✗ no field | ✓ label (0 pts) | ✗ | ✗ | ✗ | **✗** (state the authority's interface) | ✗ |
| **M10 wrong object** | **✗ no field** | — | ✗ (`BUILDER.md` §3j only, hand builds) | **✗** | ✗ | **✗** (name the protected object class) | ✗ |
| M12 variants (don't build) | ✓ lessons; Select ✓ | ✓ | ✓ "never add" | ✓ "do not add" | **✗ no ban** | — | — |
| Where vs how | ✓ lessons-v2; Select ✓ | ✗ | ✓ | ✓ "prefer how-type" | ✓ | — | — |
| Reason to dismiss (distinct per lever) | ✓ O3; Select ✓ | — | ✓ | ✓ | **✗** | ✓ (not a fairness defect) | ✓ |
| **Per-model complement** (one DeepSeek-type and one MiMo-type trap) | ✗ (lessons mention profiles) | ✗ | **✗** (`BUILDER.md` §3j only) | **✗** | **✗** | — | — |
| **No single trap carries the task** | ✗ | ✗ | **✗** | **✗** | ✗ | **✗** (post-trial) | — |
| Uses trial results (which traps each model fixed) | — | — | — | **✗ hardening gets no run data** | ✗ | ✗ (runs after the trial but never asked to read the runs) | — |

**Your guess, checked.** The screener side is mostly covered: the screening records hold fields for
most patterns, and `SELECT-PROMPT.md` scores how-type room first. The scorer file has labels for
M5, M7, M8, M9 and M11, but every label is worth 0 points and the live lanes never compute it. The
other stages split differently:
- **Builder and upgrade:** largely covered.
- **Hardening:** covers routes, second implementations, producers and coupled values, but none of
  the other mechanisms or the strategy findings.
- **Fairness and fairfix:** cover only the route-level rules (uncovered routes, layer placement,
  surface wording). They have **no pattern-specific checks**.

---

## 2. Where each missing piece is needed

Ordered by evidence. The evidence is the 13-breaker audit (`reports/breakers/13-VALIDITY-CONCERNS.md`)
and the 93-task analysis.

### P1. Fairness + fairfix: checks for coupled traps and shape traps (highest priority)

**Evidence.** Every validity problem in the 13 delivered breakers sits in a coupled or shape test:

| Task | The contradiction |
|---|---|
| litellm | a coupled test requires the opposite of the instruction's "never" |
| yamcs | a container-feed coupled test against the first rule |
| openbao | substituted `/` must be accepted although the instruction lists the path separator |
| tinacms | empty key and leading slash |
| knowns | a trailing-dot id that fits the keep-working character set |
| siyuan | disabled fixture snippets |

The fairness brief has no step that looks for this.

**Where:**
- **`FAIRNESS-REVIEW-BRIEF.md`, a new step after step 1:**
  - **Coupled trap:** for every functional test that holds a must-keep-working value next to a hidden
    one, quote the keep-working clause that states it, and check that it does not contradict any
    security rule. A keep-working demand the security rule forbids is gate a.
  - **Shape trap:** for every refused shape, check that it lies outside the legitimate set that every
    keep-working clause and fixture describes.
  - **Fixtures and harness:** the state the tests set up must be one the instruction calls legitimate
    (enabled, published, configured).
- **The same brief, using trial data.** Fairness already runs after the trial, so add: "for each
  failed run, list the tests that decided it. If one test decides a model's result, scrutinise that
  test first." That is how the 13-task audit found the problems.
- **`run_fairfix.sh`:** resolve such a contradiction the decided way: keep the instruction, change the
  test and the reference. Never add a sentence. This rule is not in the fairfix prompt today.

### P2. Hardening: trial data, the per-model complement, and the mechanism menu

**Evidence.**
- Hardening runs only on solved tasks, yet it never learns which model solved, or which traps each
  run fixed.
- The near-misses were each carried by a single trap.
- The two models miss different kinds:
  - DeepSeek: a route where the protection is absent, plus a reason to dismiss;
  - MiMo: coupled values and how-type mechanisms.

**Where (`HARDENING-PROMPT.md`, with `run_harden.sh` passing the data):**
1. **Give the agent each run's per-test results** (`verifier/results.json`) mapped to
   `manifest.traps`, plus which model solved.
2. **Rule:** add a trap of the kind the solving model misses: an absent-protection route with a
   reason to dismiss for DeepSeek; a coupled value or a how-type mechanism for MiMo.
3. **Rule:** after hardening, no single trap may carry the task. Aim for at least 2 independently
   hard traps with different reasons to dismiss.
4. **Mechanism menu, alongside the current O8/O8b/second-implementation/producer list:**
   - M4, an absent-protection route, named explicitly with its reason to dismiss;
   - M5, a merged/defaults route;
   - M7, ordering;
   - M10, wrong object.

   Each needs a one-line build rule.

### P3. Builder (`TASK-BUILD-PROMPT-v1.md` + `SELFDESIGN-PLAN.md`)

1. **The per-model complement and no-single-carry rules.** Today they exist only in `BUILDER.md` §3j,
   which only hand builds read.
2. **Reconcile Design item 3** ("input-shape variants") with "never add encoding variants": a shape
   counts only when a plausible check mishandles it, as in Select.
3. **Add M10 (wrong object) and M7 (ordering)** to the Design menu, with build rules.
4. **`SELFDESIGN-PLAN.md` still says "Add 2-4 siblings at a recurring trust decision".** That invites
   where-type volume. Reword it to "at least one how-type, the rest only as extras".

### P4. Upgrade (`UPGRADE-PROMPT.md`)

Add the M12 ban, distinct reasons to dismiss, and the per-model complement check. It already has
§2, how-type and §8.

### P5. Screener + Select (lowest priority; mostly covered)

1. **`SCREENER-PROMPT-v2.md` O8 entries:** add `protection: absent | weak | bypassed` (M4), and an
   optional mechanism tag (M-code) per route and per O8b site. Then Select can score how-type room
   from facts instead of prose.
2. **Add fields for M7 and M10.** They are optional. The data are thin (M7: 2 runs; M10: 2 of 11
   missed).
3. **`SELECT-PROMPT.md`:** add "a host that offers both a DeepSeek-type and a MiMo-type trap scores
   higher".
4. **`weights.json`:** either wire it into the live lanes or mark it as the local, round-1 scorer.
   Its trap labels are worth 0 points and nothing computes it, so as it stands it scores nothing.
   Weights for trap stacking belong in `stacking_weights.json` (`STACKING-EXPLORATION.md` §5), not
   here.

### Not worth adding

- **M3 (shared layer), M9 (fail-open) and M1 as levers.** Of 6, 9 and 99 trialled traps
  respectively, M3 and M9 were never missed and M1 only rarely.
- **M9 does belong in fairness, as a contract check:** the authority's interface must be stated.
  Round 1 showed that an unstated interface produces fail-open and refuse-all hedges.

---

## Applied 2026-10-21 (live VM; local mirror where a copy exists)

Each step was one file, pushed by an atomic swap. VM backups are `<file>.bak-claude-20261021T1930Z`;
for `run_harden.sh`, the earlier `.bak-20261021`, which is byte-identical. Nothing was blocked.

| Step | File | Change |
|---|---|---|
| 2a | `pipeline/trial_summary.py` (new) | writes `build/<slug>/trial_summary.md`: who solved, and per trap how many runs of each model left it open (current runs, else the latest archived version) |
| 2b | `pipeline/run_harden.sh` | calls `trial_summary.py` before `snapshot_experiment.sh` moves the runs |
| 2c | `builder/HARDENING-PROMPT.md` | reads the summary; adds the "target the model that solved" rule (DeepSeek-type / MiMo-type) and "no single trap may carry the task" |
| 3a | `builder/TASK-BUILD-PROMPT-v1.md` | Design item 3 is now "shape traps": a form a plausible check mishandles. Pure variants are excluded. |
| 3b | `builder/TASK-BUILD-PROMPT-v1.md` | Design items 7 (wrong object) and 8 (ordering), with build rules |
| 3c | `builder/SELFDESIGN-PLAN.md` | list every possible sibling, pick the 2-4 most complex and hardest to find, record why in `notes.md` |
| 4a | `builder/HARDENING-PROMPT.md` | menu adds the never-protected route, merged/defaults, ordering and wrong-object traps |
| 4b | `builder/TASK-BUILD-PROMPT-v1.md` | Design items 9 (never-protected route) and 10 (merged/defaults route), with build rules |
| 6a | `builder/SELECT-PROMPT.md` | "both models covered" bonus |

**Not applied, by decision:**
- the P1 fairness and fairfix checks;
- the per-model and no-single-carry rules in the builder;
- the P4 upgrade items;
- the rest of P5.

**Caveats:**
- **Already-generated `build/<slug>/BUILD-PROMPT.md` files** embed the old template, so new builds
  need them regenerated first (`pipeline/prepare_lane.py`).
- **The hardening batch running on 2026-10-21** started on the old prompt. Its later rounds use the
  new one.

## 3. Order to apply (when we decide to)

1. **P1** (fairness + fairfix). It prevents false breakers like litellm before they ship.
2. **P2** (hardening). This is where the solved tasks are converted, and it is currently blind to
   trial data.
3. **P3** (builder).
4. **P4** (upgrade).
5. **P5** (screener).
