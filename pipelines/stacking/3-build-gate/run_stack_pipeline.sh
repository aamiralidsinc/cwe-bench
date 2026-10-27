#!/bin/bash
# Stacking driver (new; the sibling pipeline's queue/lanes are not used and not modified).
# For ONE stacked slug (built from pipelines/stacking/2-prepare/build_prepare_stack.py) and its control:
#   1. build      : common/launch/drive.sh deepseek bash common/launch/run_build.sh SLUG        (unchanged sibling launcher)
#   2. check      : python3 -I pipelines/stacking/3-build-gate/check_stack.py SLUG           (stacking static check)
#   3. postbuild  : bash common/gate/postbuild.sh SLUG --listing  (2026-10-25: listing check, gate and blind fix
#                   run AT THE SAME TIME, then the blind patch check; .sound/.unsound/.gate_error/.listing_fail).
#                   With pipelines/stacking/4-listing/LISTING_ENFORCE a listing FAIL/ERROR withholds .sound (exit 3);
#                   without it the listing result is advisory (.listing_warn).
#   4. control    : only with STACK_CONTROLS=1 (scale run default: skipped); its failure never blocks SLUG. Trials run from
#                   pipelines/stacking/6-trial/stk_queue.py trial, or the unchanged
#                   common/trial/trial_set.sh 'stk-*' <deepseek|mimo> picks it up (early exit:
#                   stop a model at its first solve; 3 runs only while it keeps failing).
# Trials, post-run audits (common/audit/postmortem.py) and fairness (pipelines/stacking/7-fairness/run_fairness_stack.sh, only
# after a model fails 3/3, per the 2026-10-19 rule) are separate steps, run after this one.
#
# Usage (on the stacking VM, from the repo root, with build/SLUG/BUILD-PROMPT.md in place):
#   bash pipelines/stacking/3-build-gate/run_stack_pipeline.sh SLUG
# Progress: build/SLUG/stack_pipeline.log (one line per step). Exit 0 = SLUG marked sound (the control may or may not be).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
SLUG=${1:?usage: run_stack_pipeline.sh SLUG}
R="$CWE_ROOT"; cd "$R" || exit 1
L="build/$SLUG/stack_pipeline.log"; mkdir -p "build/$SLUG"
log() { echo "$(date -u +%FT%TZ) $SLUG $*" | tee -a "$L"; }
gate_ok() { python3 -c "import json,sys; sys.exit(0 if json.load(open('build/$1/gate_report.json')).get('passed') else 1)" 2>/dev/null; }

log "build: start (DeepSeek via common/launch/drive.sh)"
"$CWE_DRIVE" deepseek bash common/launch/run_build.sh "$SLUG" >> "$L" 2>&1
log "build: exit $(cwe_read "build/$SLUG" build-exit.txt || echo none)"
[ -f "build/$SLUG/manifest.json" ] || { log "STOP: no manifest after build"; exit 1; }

python3 -I pipelines/stacking/3-build-gate/normalize_expect.py "$SLUG" >> "$L" 2>&1 || true
log "check: stacking static check"
python3 -I pipelines/stacking/3-build-gate/check_stack.py "$SLUG" >> "$L" 2>&1 || { log "STOP: check_stack failed (see above)"; exit 1; }
CTL=$(python3 -c "import json; print((json.load(open('build/$SLUG/manifest.json')).get('stacking') or {}).get('control_slug',''))")
[ -n "$CTL" ] || { log "STOP: manifest has no stacking.control_slug"; exit 1; }

# Post-build checks, all AT THE SAME TIME (common/gate/postbuild.sh, 2026-10-25): the listing check (build
# rule 7), the gate (static, then nop/oracle/patches in parallel, with infra retries and the gate fingerprint)
# and the blind fix; then the blind patch check. It leaves .sound / .unsound / .gate_error / .listing_fail.
log "postbuild: listing + gate + blind fix in parallel"
bash common/gate/postbuild.sh "$SLUG" --listing >> "$L" 2>&1; PRC=$?
case $PRC in
  0) log "SOUND: $SLUG ready for trials" ;;
  3) # The gate passed but the instruction lists hidden traps (build rule 7). Rewrite ONLY the instruction
     # (pipelines/stacking/5-upgrade, no rebuild: tests, fix and image are unchanged, so the gate still holds;
     # UPGRADE_FORCE because the task has no .sound yet). It re-runs the listing check itself (two rounds).
     log "LISTING: instruction lists hidden traps; instruction-only rewrite (5-upgrade)"
     UPGRADE_FORCE=1 "$CWE_DRIVE" deepseek bash pipelines/stacking/5-upgrade/run_upgrade_stack.sh "$SLUG" >> "$L" 2>&1; URC=$?
     if [ "$URC" = 0 ] && python3 -I common/gate/fingerprint.py check "$SLUG" >> "$L" 2>&1; then
       cwe_unmark "build/$SLUG" .listing_fail; touch "build/$SLUG/.sound"   # touch: also refreshes an existing .sound
       log "SOUND: $SLUG ready for trials (instruction rewritten, listing PASS)"
     else
       log "LISTING: rewrite exit $URC; $SLUG stays .listing_fail for a person (see build/$SLUG/upgrade_stack.log)"; exit 3
     fi ;;
  *) log "STOP: postbuild exit $PRC for $SLUG (see build/$SLUG/postbuild.log)"; exit 1 ;;
esac
# Scale run (owner decision 2026-10-25): controls are not gated or trialled unless STACK_CONTROLS=1.
if [ "${STACK_CONTROLS:-0}" != 1 ]; then
  log "control $CTL: skipped (scale mode; set STACK_CONTROLS=1 to gate it)"; exit 0
fi
# The control is lowest priority (user, 2026-10-22): a failed control gate never blocks its stacked task.
log "gate: $CTL (control)"
if bash common/gate/gate_one_ds.sh "$CTL" >> "$L" 2>&1; then log "SOUND: $CTL (control) ready for trials"
else log "control gate failed for $CTL; the stacked task stays sound, the control is not trialled"; fi
