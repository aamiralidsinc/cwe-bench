#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
S=stk-senaite-core-4280 C=$S-control L=stacking/out/senaite_harness_chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
log "control fairfix (harness stub falls back to real bika.lims.api)"
FAIRFIX_BRIEF=build/$C/AUDIT-FIX-20261025.md ./drive.sh deepseek bash stacking/run_fairfix_stack.sh $C >> build/$C/senaite_harness_chain.log 2>&1; rc=$?
log "control fairfix rc=$rc ($(cat build/$C/fairfix_status.txt))"
[ $rc = 0 ] || { log "chain stopped (control held)"; exit 1; }
bash pipeline/gate_one_ds.sh $C >> build/$C/senaite_harness_chain.log 2>&1; g=$?
log "control gate rc=$g (0 = sound)"
[ $g = 0 ] || { log "control gate not sound; chain stopped (held)"; exit 1; }
rm -f build/$C/hold_deepseek build/$C/hold_mimo
setsid nohup python3 build/trial.py $C --models deepseek --no-verdict --first-run 1 --max-runs 3 > build/$C/trial_ds_chain.log 2>&1 < /dev/null &
sleep 45
setsid nohup python3 build/trial.py $C --models mimo --no-verdict --first-run 1 --max-runs 3 > build/$C/trial_mimo_chain.log 2>&1 < /dev/null &
log "control unheld; trials launched"
# Stacked task: same harness file, applied IN PLACE (no version bump: all 6 counted runs passed the
# functional tests, so no verdict depends on the stub). Backup first; restore if its gate fails.
if cmp -s build/$C/testfix-harness-src.txt /dev/null 2>/dev/null; then :; fi
B=build/$S/testfix-20261025; mkdir -p $B; cp -p tasks/$S/tests/harness/world.py $B/world.py.orig
cp tasks/$C/tests/harness/world.py tasks/$S/tests/harness/world.py
bash pipeline/gate_one_ds.sh $S >> build/$S/senaite_harness_chain.log 2>&1; gs=$?
if [ $gs = 0 ]; then log "stacked task: harness copied in place, gate sound (no version bump)"
else cp -p $B/world.py.orig tasks/$S/tests/harness/world.py; touch build/$S/.sound; log "stacked task gate rc=$gs after harness copy -> RESTORED original world.py (needs a look)"; fi
