#!/bin/bash
# Stacking driver (new; the sibling pipeline's queue/lanes are not used and not modified).
# For ONE stacked slug (built from stacking/build_prepare_stack.py) and its control:
#   1. build      : ./drive.sh deepseek bash run_build.sh SLUG        (unchanged sibling launcher)
#   2. check      : python3 -I stacking/check_stack.py SLUG           (stacking static check)
#   2b. listing   : ./drive.sh deepseek bash stacking/run_listing_check.sh SLUG  (build rule 7;
#                   a FAIL keeps the build but withholds .sound and writes .listing_fail, exit 3)
#   3. gate       : python3 -I builder/gate.py SLUG                    (unchanged)
#   4. blind fix  : ./drive.sh deepseek bash run_blindfix.sh SLUG      (unchanged)
#   5. mark       : build/<slug>/.sound when steps 2-4 pass; then the control is gated and marked
#                   sound on its own (its failure never blocks SLUG). Trials run from
#                   stacking/stk_queue.py trial, or the unchanged
#                   pipeline/trial_set.sh 'stk-*' <deepseek|mimo> picks it up (early exit:
#                   stop a model at its first solve; 3 runs only while it keeps failing).
# Trials, post-run audits (build/postmortem.py) and fairness (stacking/run_fairness_stack.sh, only
# after a model fails 3/3, per the 2026-10-19 rule) are separate steps, run after this one.
#
# Usage (on the stacking VM, from $HOME/cwe-bench, with build/SLUG/BUILD-PROMPT.md in place):
#   bash stacking/run_stack_pipeline.sh SLUG
# Progress: build/SLUG/stack_pipeline.log (one line per step). Exit 0 = SLUG marked sound (the control may or may not be).
set -uo pipefail
SLUG=${1:?usage: run_stack_pipeline.sh SLUG}
R="$HOME/cwe-bench"; cd "$R" || exit 1
L="build/$SLUG/stack_pipeline.log"; mkdir -p "build/$SLUG"
log() { echo "$(date -u +%FT%TZ) $SLUG $*" | tee -a "$L"; }
gate_ok() { python3 -c "import json,sys; sys.exit(0 if json.load(open('build/$1/gate_report.json')).get('passed') else 1)" 2>/dev/null; }

log "build: start (DeepSeek via drive.sh)"
./drive.sh deepseek bash run_build.sh "$SLUG" >> "$L" 2>&1
log "build: exit $(cat "build/$SLUG/build-exit.txt" 2>/dev/null || echo none)"
[ -f "build/$SLUG/manifest.json" ] || { log "STOP: no manifest after build"; exit 1; }

python3 -I stacking/normalize_expect.py "$SLUG" >> "$L" 2>&1 || true
log "check: stacking static check"
python3 -I stacking/check_stack.py "$SLUG" >> "$L" 2>&1 || { log "STOP: check_stack failed (see above)"; exit 1; }
CTL=$(python3 -c "import json; print((json.load(open('build/$SLUG/manifest.json')).get('stacking') or {}).get('control_slug',''))")
[ -n "$CTL" ] || { log "STOP: manifest has no stacking.control_slug"; exit 1; }

# Listing check (build rule 7, 2026-10-24): does instruction.md list the hidden traps? Read-only and
# cheap, so it runs before the gates; one retry on a review error. The result decides .sound below.
log "listing: check"
for try in 1 2; do
  ./drive.sh deepseek bash stacking/run_listing_check.sh "$SLUG" >> "$L" 2>&1
  python3 -I stacking/listing_verdict.py "$SLUG" >> "$L" 2>&1; LST=$?
  [ "$LST" -ne 2 ] && break
done
log "listing: $(python3 -I stacking/listing_verdict.py "$SLUG" | head -1)"

log "gate: $SLUG"
python3 -I builder/gate.py "$SLUG" >> "$L" 2>&1
gate_ok "$SLUG" || { log "STOP: gate failed for $SLUG"; exit 1; }

log "blind fix: $SLUG"
./drive.sh deepseek bash run_blindfix.sh "$SLUG" >> "$L" 2>&1
python3 -I builder/gate.py "$SLUG" --only patches >> "$L" 2>&1
gate_ok "$SLUG" || { log "STOP: patch checks failed after the blind fix"; exit 1; }

if [ "$LST" -ne 0 ]; then
  rm -f "build/$SLUG/.sound"; touch "build/$SLUG/.listing_fail"
  log "LISTING: $SLUG is gated but its instruction lists hidden traps (or the check errored); not marked sound. Rewrite the instruction (build rule 7), re-run stacking/run_listing_check.sh, then mark it."
  exit 3
fi
rm -f "build/$SLUG/.listing_fail"
touch "build/$SLUG/.sound"
log "SOUND: $SLUG ready for trials"
# The control is lowest priority (user, 2026-10-22): a failed control gate never blocks its stacked task.
log "gate: $CTL (control)"
python3 -I builder/gate.py "$CTL" >> "$L" 2>&1
if gate_ok "$CTL"; then touch "build/$CTL/.sound"; log "SOUND: $CTL (control) ready for trials"
else log "control gate failed for $CTL; the stacked task stays sound, the control is not trialled"; fi
