# Stacking fairness addendum, v1, 2026-10-22

**How it is used:**
- **Fairness review:** appended to `builder/FAIRNESS-REVIEW-BRIEF.md` when the task's
  `build/<slug>/manifest.json` has a `stacking` block.
- **Fairfix:** also appended to the fairfix prompt for such tasks.
- **Origin:** these checks are the ones the 13-breaker audit found missing
  (`reports/breakers/13-VALIDITY-CONCERNS.md`); every contradiction there sat in a coupled or a shape
  test. They are needed most for stacked tasks, which carry many coupled tests.

---8<---

## Additional checks for a stacked task

This task stacks several independent concepts; `manifest.stacking` lists them. Add a section
**"Stacking checks"** to FAIRNESS.md with one row per check below and per concept.

**S1. Coupled traps (gate a when it fails).** For every functional test holding a must-keep-working
value next to a hidden one:
- quote the instruction clause that states that value;
- check that the clause does not contradict any security rule in the instruction.

A keep-working demand that a security rule forbids, read literally, is a contradiction: a correct fix
cannot pass both.

**S2. Shape traps (gate a when it fails).** For every input shape a security test refuses, check that
it lies outside the legitimate set that every keep-working clause, example and fixture describes.
Two examples: a refused name ending in a dot, where the stated legitimate character set allows it; a
refused leading slash, where another route must accept it.

**S3. Fixtures and harness (gate a when it fails).**
- Every state the tests set up must be one the instruction calls legitimate (enabled, published,
  configured, authorised).
- The harness must reach each concept through its real entry point, so a correct guard placed at any
  valid layer passes.

**S4. Concept independence (gate a when it fails).**
- A correct fix for concept X must pass all of X's tests whatever the state of the other concepts.
- For masking (H3c): the masked concept's security test must fail on the pinned code through its own
  route.

**S5. History (gate a when it fails).**
- **For H3a / H3b:** `checks/upstream_first_fix.patch` must violate the instruction's property read
  literally, not merely differ from the reference. If upstream's first fix satisfies the property
  as written, the property is too narrow or the later bug is out of scope: widen the property in
  general terms, or drop that concept.
- **For a dependency-bump fix (F5):** an in-repo fix exists (the reference proves it), and the
  instruction never requires an upgrade.

**S6. Contracts (gate a only when a correct fix cannot pass).**
- Tests must not need a field or function name the solver would have to guess.
- For a wrong-object trap, the protected object class is named in product terms.
- For a fail-open fallback, the authority's interface is stated.

**S7. Decisive tests (after the trial; NEEDS_HUMAN_REVIEW when it fires).**
- Read `build/<slug>/trial_summary.md` if it exists.
- For each failed run, list the tests that decided it.
- If a single test decides a model's result, re-check that test first against S1-S6, and set
  NEEDS_HUMAN_REVIEW: YES with that test named.

**Fairfix rules for stacked tasks:**
- Resolve a contradiction by keeping the instruction and changing the test and the reference
  (decision of 2026-10-20). Never add a sentence that points at a route.
- Drop a concept only when the concept itself cannot be made fair. If fewer than 3 independent
  concepts remain, the task is no longer a stacked task: report that, rather than shipping it.
