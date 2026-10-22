#!/bin/bash
# Fairness-fix one built task: apply its pre-trial fairness review's REQUIRED changes, then re-gate.
# Needs Bash+Docker (edits tests/oracle, runs gate) -> bypassPermissions -> a PERSON launches this.
# Usage: run_fairfix.sh SLUG   Env: MODEL (default claude-opus-5-5), FAIRFIX_TIMEOUT (default 10800)
set -uo pipefail
SLUG=$1
cd "$HOME/cwe-bench" || exit 1
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
P="You are revising ONE already-built security-fix benchmark task to address its pre-trial FAIRNESS
review before model trials. Project root: /home/mara/cwe-bench. Task slug: ${SLUG}.

Read, in order: build/${SLUG}/FAIRNESS.md (the review, with a numbered 'Required changes' list),
builder/FAIRNESS-REVIEW-BRIEF.md (what fairness means here), tasks/${SLUG}/instruction.md,
tasks/${SLUG}/tests/ (all files), tasks/${SLUG}/solution/fix.patch, build/${SLUG}/manifest.json,
build/${SLUG}/notes.md, build/${SLUG}/checks/*.patch.

Apply EVERY 'Required' change in FAIRNESS.md (and any 'Recommended' change that is cheap and clearly
safe). These typically mean: remove sentences in instruction.md that name a file/function/trap/
mechanism/variant-list/count or otherwise hint the fix; add or loosen/tighten security or functional
tests exactly as the review specifies; add the check patches it names (checks/*.patch) and wire them
into manifest.patch_checks with the stated expect; extend solution/fix.patch and any alternative
patch where the review says the oracle is incomplete; align the instruction with what the oracle and
tests actually deliver; update manifest traps/leak_terms to match any added tests/patches.

Hard rules:
- Keep the task valid: the pinned code must still FAIL every security test (nop), and the oracle
  (solution/fix.patch) must still PASS all tests (oracle). Do not weaken a test merely to make
  something pass; follow the review's intent (fair, findable, leniency-tight).
- Behavioural tests through the real entry point; expected values computed in the test; no network;
  do not look up the upstream fix; keep instruction.md free of manifest.leak_terms.
- Never add a sentence that describes where a sibling, far site or uncovered route lives, even in
  product terms (a route, operation, command, channel, object kind, stage or format), and never
  list them. When a test needs coverage in the instruction, widen the one general property over
  the protected data or outcome. Apply every item under 'Required: generalize' in FAIRNESS.md.
- Never 'fix' a real unfixed upstream route, or a route where the protection never existed, by
  removing it, its tests or its trap, or by adding a sentence that points at it. Such a route is
  fair when the general property covers it. Repair only real defects: wording that excludes the
  route (widen the property in general terms), or a test that fails a correct fix (make it drive
  the real entry point and assert the outcome, accepting any refusal the instruction allows).
- Edit only under tasks/${SLUG}/ and build/${SLUG}/. Scratch in ~/.tb-graders/cwe/work/${SLUG}/.

Then run the gate yourself, one stage at a time, and iterate until all pass:
  python3 -I builder/gate.py ${SLUG} --only static
  python3 -I builder/gate.py ${SLUG} --only nop
  python3 -I builder/gate.py ${SLUG} --only oracle
  python3 -I builder/gate.py ${SLUG} --only patches
A missing blind.patch in static is allowed (it is wired separately). Report, under 300 words: each
FAIRNESS 'Required' item and how you addressed it, the final gate result per stage, and any item you
could not fully satisfy and why."
date -u +%FT%TZ > "build/$SLUG/fairfix_start.txt"
timeout "${FAIRFIX_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$P" --model "${MODEL:-claude-opus-5-5}" \
  --permission-mode bypassPermissions --add-dir "$HOME/cwe-bench" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "build/$SLUG/fairfix-run.json" 2> "build/$SLUG/fairfix-run.err"
echo $? > "build/$SLUG/fairfix-exit.txt"
date -u +%FT%TZ > "build/$SLUG/fairfix_end.txt"
echo "$SLUG fairfix: exit $(cat build/$SLUG/fairfix-exit.txt)"
