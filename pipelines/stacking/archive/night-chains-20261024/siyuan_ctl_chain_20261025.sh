#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
S=stk-siyuan-ghsa4mx9 C=$S-control L=stacking/out/siyuan_ctl_chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
log "wait for the stacked task's second repair to finish"
while ps -eo args | grep -q "[r]un_fairfix_stack.sh $S\$"; do sleep 60; done
log "task fairfix status: $(cat build/$S/fairfix_status.txt)"
FAIRFIX_BRIEF=build/$C/AUDIT-FIX-20261025.md ./drive.sh deepseek bash stacking/run_fairfix_stack.sh $C >> build/$C/siyuan_ctl_chain.log 2>&1; rc=$?
log "control fairfix rc=$rc ($(cat build/$C/fairfix_status.txt))"
[ $rc = 0 ] || { log "chain stopped (control held)"; exit 1; }
bash pipeline/gate_one_ds.sh $C >> build/$C/siyuan_ctl_chain.log 2>&1; g=$?
log "control gate rc=$g (0 = sound)"
[ $g = 0 ] || { log "control gate not sound; chain stopped (held)"; exit 1; }
rm -f build/$C/hold_deepseek build/$C/hold_mimo
setsid nohup python3 build/trial.py $C --models deepseek --no-verdict --first-run 1 --max-runs 3 > build/$C/trial_ds_chain.log 2>&1 < /dev/null &
sleep 40
setsid nohup python3 build/trial.py $C --models mimo --no-verdict --first-run 1 --max-runs 3 > build/$C/trial_mimo_chain.log 2>&1 < /dev/null &
log "control unheld; trials launched"
