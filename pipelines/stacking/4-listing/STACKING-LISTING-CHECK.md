# Stacking listing check (post-build), v3, 2026-10-24

**v2 (2026-10-24, after the first calibration):** v1 labelled the general property itself DESCRIBED
(it read "a sentence that covers a whole class of traps" and "when unsure, choose the label closer to
NAMED" literally), so it failed instructions the audit passes. v2 makes the property and its general
clarifications GENERAL, applies the one-bug test to GENERAL-vs-DESCRIBED doubts, and adds two cases v1
missed: lists of operations or resources (DESCRIBED) and keep-working lines that reproduce the coupled
tests item by item (NAMED). v3: scope-widening clauses over parts of the system that only
hidden traps occupy are DESCRIBED.

**Calibration (2026-10-24, `pipelines/stacking/out/calibration-listing/`):** v1 matched the batch-1 audit on 4 of 5
verdicts (too strict on the general property); v2 on 10 of 11; v3 on 17 of 17 (11 seen + 6 held out),
trap labels 59 of 63, more lenient than the audit on 2 of 63 (3%). Caveat: batch 1 has only one
instruction the audit passes (lobe-chat), so the false-FAIL rate on clean instructions is measured on
one task; watch the first v2-addendum builds.

**What it is:** a read-only review that runs after `check_stack.py`. It classifies how a stacked
task's instruction covers each hidden trap, and enforces build rule 7 of
`STACKING-BUILD-ADDENDUM.md`.

**Why:**
- In batch 1 (30 tasks), 137 of 155 traps had a sentence of their own in instruction.md
  (`pipelines/stacking/out/listing_audit.json`), so the tasks read as checklists.
- 9 of the 22 sound tasks were solved by both models, mostly on the first run.

**How it runs:**
- **Launcher:** `pipelines/stacking/4-listing/run_listing_check.sh`. It writes `build/<slug>/listing.json`.
- **Verdict:** `pipelines/stacking/4-listing/listing_verdict.py <slug>`.
  - It reads the trap origins from `manifest.json`, not from the reviewer.
  - **Exempt:** traps with origin `advisory_route`, the reported bug, which the impact example may
    show.
  - **FAIL:** one NAMED hidden trap, or more than one DESCRIBED hidden trap.
  - **ERROR:** no finished review, a hidden trap without a label, or a label outside the four.
- **Gating (2026-10-24):** advisory until the reviewer is calibrated. Without `pipelines/stacking/4-listing/LISTING_ENFORCE`
  a FAIL or ERROR writes `build/<slug>/.listing_warn` and the task is marked sound as before; with it,
  `.listing_fail` and no `.sound`. To calibrate: run the check on batch-1 tasks, then
  `python3 -I pipelines/stacking/4-listing/listing_calibrate.py SLUG... [--enforce]` (every verdict must match the audit, and
  at most 10% of hidden traps may be labelled more leniently than the audit).
- **Integrity:** the reviewer has the Write tool, so the launcher snapshots `tasks/<slug>/`,
  `manifest.json` and `checks/` first and restores them if the review changed anything (counts as not
  finished).

---8<---

## Listing check: does this instruction list its hidden traps?

You are reviewing ONE security-fix task. A solver sees only `instruction.md`. It must find several
hidden traps on its own: routes, forms, sources or coupled values. The concern is that the
instruction lists those traps, so the task becomes a checklist.

**Read:**
- `{{ROOT}}/tasks/{{SLUG}}/instruction.md`, which the solver sees;
- the `traps` list in `{{ROOT}}/build/{{SLUG}}/manifest.json`: each trap's `id`, `origin`, `shape`,
  `where` and `coupled_functional_tests`.

Read nothing else.

**Classify EVERY trap in `manifest.traps`, exactly one label each:**
- **NAMED:** the instruction names the trap's surface. That means a concrete identifier pointing at
  where the trap is: an endpoint, route, alias, file, function, field, parameter, config key,
  header, input form, encoding, or a literal example value.
- **DESCRIBED:** no identifier, but some sentence or clause describes this trap's distinguishing
  shape, mechanism, timing, source or legitimate value. The test is whether that sentence would be in
  the instruction if the task had only the advisory's own route. If not, the trap is DESCRIBED.
  Examples:
  - "for every form in which the lease can be named";
  - "both when the value is supplied and again when a call is about to connect";
  - "whichever provider response supplies that address";
  - "a string such as `"true"`";
  - a keep-working line such as "names may contain dots" or "short and hyphenated names";
  - a list of operations, actions, resources, stages or forms (for example "when it is created,
    renamed, or exported"), even when it reads as product terms.

  A sentence that singles out a group of traps by a feature the property alone does not imply (a
  form, a stage, a second implementation, a kind of input) counts as DESCRIBED for each trap in the
  group. So does a scope-widening clause over a part of the system that only hidden traps occupy
  ("whatever the component involved", "in every storage backend", "at every step of the flow"):
  the advisory's own route lives in one component, so a one-bug version would not need the clause.
  "However it is supplied" stays GENERAL only when it is about how the protected value arrives.
- **GENERAL:** covered only by wording that a one-bug version of the task would also have. That
  means:
  - the general property itself and its general clarifications, phrased over the protected data or
    outcome. These are GENERAL for every trap they cover, even when they are the reason the trap is
    in scope. Examples of this kind: "the protection applies to the value itself, whatever request
    carries it"; "who owns a record is decided from the stored record, never from what the caller
    sends"; "any input a caller controls that ends up in the protected operation is covered";
  - "however it is supplied", "every legitimate use keeps working", the refusal form, or an operator
    opt-in.

  The difference from DESCRIBED: a GENERAL sentence would read the same with only the advisory's own
  route in the task; a DESCRIBED sentence points the solver at something it would not look for from
  the property alone.
- **ABSENT:** not covered at all, not even by a general rule.

**Coupled values:**
- For a trap with `coupled_functional_tests`, also judge the keep-working and contract lines.
- If a line names or describes that trap's legitimate value, the trap is at least DESCRIBED.
  If it gives the literal value, or lists the coupled tests' cases item by item, the trap is NAMED.

**Judge only the text**, not what a solver might infer. When unsure between GENERAL and DESCRIBED,
apply the one-bug test literally: if a well-written one-bug version of this task could contain the
sentence word for word, it is GENERAL; otherwise DESCRIBED. When unsure between DESCRIBED and NAMED,
choose NAMED.

**Write `{{ROOT}}/build/{{SLUG}}/listing.json`, and nothing else**, as one JSON object:

```json
{"slug": "{{SLUG}}",
 "traps": [{"id": "<manifest trap id>", "coverage": "NAMED|DESCRIBED|GENERAL|ABSENT",
            "quote": "<the shortest instruction phrase behind the label; empty for GENERAL/ABSENT>",
            "note": "<one line>"}],
 "instruction_words": <int>}
```

Every trap id in `manifest.traps` must appear exactly once. Do not change any other file.
