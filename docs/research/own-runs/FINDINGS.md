# Own runs: what made DeepSeek and MiMo pass or fail (19 tasks, 121 graded runs)

Analysis date 2026-10-16. Verdicts come only from `build/audit/trials.tsv` (audit_results.py). The
evidence is in this folder:
- `matrix.md`: per test, per model
- `task_table.md`: task properties against results
- `lookups.tsv`: internet lookups per run
- `raw/`: three transcript deep-dives, written by agents and spot-checked

## Bottom line

1. **Most of our failures are test faults, not model failures.** All of these runs fixed the
   vulnerability or blocked the attack; our tests checked something the instruction never asked for:
   - **actualbudget MiMo 0/3:** the test calls the product's `getPathForUserFile` to find where an
     escaped file would land. MiMo hardened that helper, so the test crashes before it sends a
     request. Verified in the verifier output.
   - **stigmem v2/v3:** the instruction says "bound to a non-loopback address"; the tests vary the
     advertised `node_url`. Verified.
   - **stigmem v4:** the test calls an internal function directly with an explicit
     `signing_required=False`.
   - **trigger-dev realtime write:** the test accepts only HTTP 405 (route deleted), but a 401 also
     blocks the attack. Verified.
   - **trigger-dev check-completion:** a functional test expects 302/200 for a batch that doesn't
     exist; a stricter fix returns 403.
   - **argo webhook:** the test needs a 5 MiB body rejected, using a 2 MB limit that appears only
     upstream. MiMo chose 10 MiB, with a stated reason.
2. **Only one per-model failure is genuine: jackson-databind-sib / DeepSeek 0/6.** In all six runs
   DeepSeek thought of the any-setter path within a minute. It then dismissed it, because that code
   has *no* view checks at all, and read the missing check, which *is* the vulnerability, as proof
   the case couldn't happen. It never ran a probe. MiMo tests a doubtful case by running code, and
   found it.
3. **Looking up the upstream fix is the main way models pass.** Runs that fetched the advisory or
   fix from GitHub solved 43 of 44 (98%); runs that didn't solved 40 of 62 (65%). For stacking it
   was 16/17 against 4/13. A lookup also copies upstream's exact choices (status codes, limits,
   layer), which is precisely what our faulty tests demand. **No jackson-family run looked
   anything up**, because the injected siblings have no upstream fix, and that is where the only
   genuine failure is.
4. **Instruction wording decided jackson-sib7.** Its instruction adds two sentences listing the
   any-setter declaration forms. DeepSeek found the siblings in 10 of 11 sib7 runs and 0 of 6 sib
   runs. More siblings had nothing to do with it.
5. **Stacking added volume, not difficulty.** Every item in every stacking task was located in
   every run. Fix order varied and made no difference.
6. **Over-broad fixes are common.** 8 of 26 jackson runs (both models) hid a linked, permitted
   property (`visibleTypeIdCreatorPropStillBound`), and MiMo's stigmem config gate refused the
   loopback setups it must allow.
7. **Infrastructure:** MiMo jackson-databind-sib `gUSEhL9` (0/8) ended on a provider "considered
   high risk" refusal after one edit. That isn't a model result.

## Where the per-model failures stand after this analysis

| Pair | Ledger now | What really happened | Valid? |
|---|---|---|---|
| actualbudget / MiMo | failed 0/3 (0.9 each) | fixed all 10 items; test 02 crashes on MiMo's hardened helper | **No:** test fault |
| stigmem / MiMo | failed 0/3 | implemented every item; v2/v3 keyed on the bind host as the instruction says, v4 test layer | **No:** test/instruction mismatch |
| jackson-databind-sib / DeepSeek | failed 0/6 | dismissed the any-setter siblings in every run | **Yes** |
| (solved pairs) trigger-dev / DeepSeek 1/3; stigmem / DeepSeek 2/3; argo / MiMo 1/2; jackson-databind-sib / MiMo 1/3 | – | failing runs hit the test faults above, or a provider stop | failing runs invalid; verdicts unchanged |

## Implications

### Test and gate quality (fix before anything else)

- **Tests must not call product code the agent can change**, whether to compute expected values or
  to clean up. Gate rule: tests import only the harness and public entry points.
- **Assert that the attack is blocked, not how.** Accept any 4xx or refusal; no exact status codes,
  and no limits or constants taken from upstream unless the instruction states them.
- **Test each item at the layer the instruction names.** stigmem v5 was tested at startup and
  passed 8 of 8; v4 was tested at an internal function.
- **New gate: a fix written from the instruction alone.** A blind agent gets only
  `instruction.md`, writes a fix, and must score 1.0. Today's alternative fixes were written by
  someone who knew the reference.
- **New gate: a defensive-hardening variant.** The reference fix plus hardening of shared helpers
  must still pass.
- **New gate: instruction leak check.** If a model given only the instruction can name the
  sibling's mechanism, rewrite the instruction (the sib7 lesson).
- **Audit:** a provider safety refusal makes the run ungraded, not a fail.

### Screening

- **Mined and stacked public advisories are solved by lookup** under open internet, at 96–100%
  in mined tasks. Screening them for difficulty matters less than making them un-lookupable.
- **Coupled bindings** ("hide A but keep a linked B working") produce over-broad fixes in both
  models. That's worth a screener signal and a functional test in every variant.
- The finding from items 1–5 still holds (abstract or broad weaknesses are harder), but our runs
  show the dominant factor is **whether a public fix exists to copy**.

### Sibling injection: our only real lever

- **Siblings must be at places the upstream patch never touches**, so a diff against upstream
  can't reveal them. That's the one thing a lookup cannot answer.
- **Siblings where the feature lacks the check entirely beat DeepSeek, not MiMo.** DeepSeek
  reasons "no checks here, so out of scope"; MiMo runs a probe. To beat both, make the probe
  inconclusive: one skipped call site in a feature that is otherwise checked, so a quick test of
  the common path passes.
- **Describe the class of bug, never the instances.** Name the security property, not the
  declaration forms or code paths.
- **Candidate sibling sites from these runs:**
  - a second caller of stigmem's plugin loading (the CLI path stayed open in two runs)
  - a second legacy write route in trigger-dev
  - another dashboard action with a real cross-tenant test

### Stacking

- **Don't stack items from one upstream security release.** One lookup reveals them all
  (stigmem's 3 fix commits, trigger-dev's PRs).
- **Stack items that need different reasons to be missed** (dismissed, wrong layer, over-broad),
  not just more items. 5–6 well-described advisories were all found.
- **Check that the stack is really several concepts.** A gate patch that guards only the lowest
  shared function must fail; if it passes, the stack is one fix. MiMo closed all five sib7 siblings
  inside `SettableAnyProperty`.
- **Measure stacking properly:** re-run the sib7 sibling set with the sib instruction.

## Proposed corrections (need a decision)

1. **Repair the faulty tests:** actualbudget 02, argo webhook size, stigmem v2/v3/v4, trigger-dev
   realtime write (any 4xx) and check-completion (accept 403).
2. **Fix the verdicts:**
   - Regrade runs whose final code was saved: stigmem MiMo r2/r3, trigger-dev DeepSeek r2/r4,
     jackson-sib runs with `final-code/`.
   - Re-run the pairs with no saved code: actualbudget MiMo ×3.
   - Record the provider-stop run as ungraded.
3. **Add the four gates** above to `builder/gate.py`.

## Limits

- 19 tasks; most solved pairs have 1–3 runs.
- Lookup detection is a transcript scan (`lookup_scan.py`). It may miss lookups made through other
  tools and counts any advisory search as a lookup.
- The three deep-dives are agent reports. I verified their key claims (actualbudget helper crash,
  stigmem `node_url`, trigger-dev 405, sib7 instruction text, the MiMo provider stop); other
  details are unverified.
- Runs before 2026-10-15 kept no final code, so their fixes are known only from transcripts.
