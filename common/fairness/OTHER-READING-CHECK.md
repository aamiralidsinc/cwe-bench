# Other-reading check: a repair step (owner, 2026-10-28)

This step proves or clears a flagged conflict by running code instead of arguing about it. It is part of the
REPAIR step, not a generic gate stage.

- **Used by:** both fairfix prompts (`pipelines/sibling/10-fairfix/run_fairfix.sh` and
  `pipelines/stacking/8-fairfix/run_fairfix_stack.sh`), and by any person or agent repairing a test under
  `pipelines/router/ORCHESTRATOR.md` §5.4.
- **What is sent:** only the text below the marker.
- **Gate:** `common/gate/gate.py` (`kind: "other_reading"`).
- **Delivery reader:** `common/fairness/fairness_verdict.py` (`conflicts_proven`).

---8<---

## Other-reading check (do this for every flagged conflict)

Run this step for every test that a fairness review (its Conflicts table) or a post-run audit
(`unfair_kind: "conflict"`) flags as a conflict and marks as deciding, meaning it decided at least one
run.

1. **Write the fix that follows the other reading.** Save it as
   `build/<slug>/checks/other_reading_<short-name>.patch`.
   - Start from `solution/fix.patch`.
   - Change only what is needed to follow the OTHER instruction sentence, the one the test does not side
     with. The result must be a correct fix a competent engineer could write from that sentence.
   - Everything else stays as in the reference.
2. **Declare it** in `build/<slug>/manifest.json` `patch_checks`:
   ```json
   {"patch": "other_reading_<short-name>.patch", "kind": "other_reading", "expect": "other_reading",
    "tests": ["<each flagged test id, as the gate's results name it>"],
    "follows": "<the instruction sentence the patch follows, quoted>",
    "flagged_by": "<build/<slug>/FAIRNESS.md, or the postmortem folder>"}
   ```
3. **Run the patches stage:** `python3 -I common/gate/gate.py <slug> --only patches`. The result never makes
   the task unsound. For each named test the gate reports:
   - **PASS: no conflict.** The test accepts a fix that follows the other sentence. Say so in your report;
     the flag was wrong.
   - **FAIL: conflict proven.** The gate prints `[gate] CONFLICT-PROVEN: <test>` and records the test under
     `conflict_proven` in `gate_report.json`. The test is unfair, and the task cannot be delivered until
     the test is repaired.
   - **MISSING: nothing proven.** No result carries that test id. Fix the id in `tests`.
4. **Repair a proven conflict in the tests only.** Keep `instruction.md` unchanged and change the test, and
   the reference if needed.
   - Make the test accept both readings, or drop the case.
   - Keep the originals and a `README.md` in `build/<slug>/repaired-tests-<YYYYMMDD>/` (for a removal:
     `removed-tests-<YYYYMMDD>/`). The README names the other_reading check. Do not write the outcome into
     `notes.md` (build facts only); a step record goes to `build/<slug>/history/<YYYYMMDD>-repair.md`.
   - Leave the check declared, so the re-gate runs it again and shows PASS (or MISSING for a removed test).
5. **Do not argue a FAIL away** in prose or in `HUMAN-DECISION.md`. A `CONFLICTS-RULED` line does not
   clear a proven conflict; only a test repair followed by a re-gate does.
