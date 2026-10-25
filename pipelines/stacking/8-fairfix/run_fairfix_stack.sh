#!/bin/bash
# STACKING COPY of pipelines/sibling/10-fairfix/run_fairfix.sh (original untouched). Differences: appends
# pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md (incl. its fairfix rules) to the prompt; project root from $HOME.
# Fairness-fix one built task: apply its pre-trial fairness review's REQUIRED changes, then re-gate.
# Needs Bash+Docker (edits tests/oracle, runs gate) -> bypassPermissions -> a PERSON launches this.
# Usage: common/launch/drive.sh deepseek bash pipelines/stacking/8-fairfix/run_fairfix_stack.sh SLUG   Env: MODEL (required, set by common/launch/drive.sh),
# FAIRFIX_TIMEOUT (default 10800). Exit 0 = the agent finished; 1 = it did not (fairfix_status.txt
# says why: quota, API error, timeout, crash) and the task must not be treated as fixed.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: pipelines/stacking/8-fairfix/run_fairfix_stack.sh SLUG}
cd "$CWE_ROOT" || exit 1
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; launch via common/launch/drive.sh deepseek bash pipelines/stacking/8-fairfix/run_fairfix_stack.sh $SLUG" | tee "build/$SLUG/fairfix_status.txt"; exit 1; }
# FAIRFIX_BRIEF (2026-10-24): a brief with a numbered 'Required changes' list to apply INSTEAD of the
# pre-trial review, e.g. a post-trial audit's repair (build/SLUG/AUDIT-FIX-*.md). Unset = FAIRNESS.md.
BRIEF=${FAIRFIX_BRIEF:-build/${SLUG}/FAIRNESS.md}
[ -f "$BRIEF" ] || { echo "error: brief $BRIEF missing" | tee "build/$SLUG/fairfix_status.txt"; exit 1; }
BN=$(basename "$BRIEF")
echo "running" > "build/$SLUG/fairfix_status.txt"
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
bash "$CWE_SNAPSHOT" "$SLUG"  # preserve prior version before in-place edit (provenance)
P="You are revising ONE already-built security-fix benchmark task to address its FAIRNESS
review before model trials. Project root: $CWE_ROOT. Task slug: ${SLUG}.

Read, in order: ${BRIEF} (the review or audit brief, with a numbered 'Required changes' list),
common/fairness/FAIRNESS-REVIEW-BRIEF.md (what fairness means here), tasks/${SLUG}/instruction.md,
tasks/${SLUG}/tests/ (all files), tasks/${SLUG}/solution/fix.patch, build/${SLUG}/manifest.json,
build/${SLUG}/notes.md, build/${SLUG}/checks/*.patch.

Apply EVERY 'Required' change in ${BN} (and any 'Recommended' change that is cheap and clearly
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
  the protected data or outcome. Apply every item under 'Required: generalize' in ${BN}.
- Never 'fix' a real unfixed upstream route, or a route where the protection never existed, by
  removing it, its tests or its trap, or by adding a sentence that points at it. Such a route is
  fair when the general property covers it. Repair only real defects: wording that excludes the
  route (widen the property in general terms), or a test that fails a correct fix (make it drive
  the real entry point and assert the outcome, accepting any refusal the instruction allows).
- Edit only under tasks/${SLUG}/ and build/${SLUG}/. Scratch in ~/.tb-graders/cwe/work/${SLUG}/.

Then run the gate yourself, one stage at a time, and iterate until all pass:
  python3 -I common/gate/gate.py ${SLUG} --only static
  python3 -I common/gate/gate.py ${SLUG} --only nop
  python3 -I common/gate/gate.py ${SLUG} --only oracle
  python3 -I common/gate/gate.py ${SLUG} --only patches
A missing blind.patch in static is allowed (it is wired separately). Report, under 300 words: each
${BN} 'Required' item and how you addressed it, the final gate result per stage, and any item you
could not fully satisfy and why."
P="$P

This is a STACKED task. Also apply these rules:
$(sed -n "/^---8<---$/,\$p" pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md | tail -n +2)"
date -u +%FT%TZ > "build/$SLUG/fairfix_start.txt"
timeout "${FAIRFIX_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --permission-mode bypassPermissions --add-dir "$CWE_ROOT" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "build/$SLUG/fairfix-run.json" 2> "build/$SLUG/fairfix-run.err"
rc=$?
echo $rc > "build/$SLUG/fairfix-exit.txt"
date -u +%FT%TZ > "build/$SLUG/fairfix_end.txt"
st=$(python3 "$CWE_AGENT_STATUS" "build/$SLUG/fairfix-run.json" "$rc" --details "build/$SLUG/fairfix_status.json")
echo "$st" > "build/$SLUG/fairfix_status.txt"
echo "$SLUG fairfix: exit $rc; $st"
# An unfinished fairfix may leave a half-edited task: put back the version that was trialed.
[ "$st" = ok ] || { bash "$CWE_RESTORE" "$SLUG" "fairfix: $st"; exit 1; }

# Build rule 13 (2026-10-24): the control has the same report as the stacked task. A fairfix that changed
# instruction.md is copied to the control (snapshotted first, for provenance), then the listing check is
# re-run on the new wording (fairness addendum, fairfix rules). The control's tests are not touched.
CTL=$(python3 -c "import json,sys; print((json.load(open(sys.argv[1])).get('stacking') or {}).get('control_slug',''))" "build/$SLUG/manifest.json" 2>/dev/null)
if [ -n "$CTL" ] && [ -f "tasks/$CTL/instruction.md" ] && ! cmp -s "tasks/$SLUG/instruction.md" "tasks/$CTL/instruction.md"; then
  bash "$CWE_SNAPSHOT" "$CTL"
  cp "tasks/$SLUG/instruction.md" "tasks/$CTL/instruction.md"
  echo "$(date -u +%FT%TZ) fairfix changed tasks/$SLUG/instruction.md; copied it to tasks/$CTL/instruction.md (rule 13)" | tee -a "build/$SLUG/control_sync.log"
fi
bash pipelines/stacking/4-listing/run_listing_check.sh "$SLUG" > /dev/null 2>&1   # MODEL is already set by common/launch/drive.sh
echo "$SLUG listing check after fairfix: $(python3 -I pipelines/stacking/4-listing/listing_verdict.py "$SLUG" | head -1)"
