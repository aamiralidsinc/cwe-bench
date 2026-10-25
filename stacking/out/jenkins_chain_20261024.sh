#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
S=stk-jenkins-ghsa7fpg C=$S-control L=stacking/out/jenkins_chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
log "wait for the running jenkins harbor run to exit"
while ps -eo args | grep -q "[h]arbor run -p /home/mara/cwe-bench/tasks/$S "; do sleep 30; done
log "fairfix (harness persistable) start"
FAIRFIX_BRIEF=build/$S/AUDIT-FIX-20261024.md ./drive.sh deepseek bash stacking/run_fairfix_stack.sh $S >> build/$S/jenkins_chain.log 2>&1; rc=$?
log "fairfix rc=$rc ($(cat build/$S/fairfix_status.txt))"
[ $rc = 0 ] || { log "chain stopped"; exit 1; }
bash pipeline/gate_one_ds.sh $S >> build/$S/jenkins_chain.log 2>&1; g=$?
bash pipeline/gate_one_ds.sh $C >> build/$S/jenkins_chain.log 2>&1; gc=$?
log "gate task rc=$g control rc=$gc (0 = sound)"
[ $g = 0 ] || { log "task gate not sound; chain stopped (holds kept)"; exit 1; }
rm -f build/$S/hold_deepseek build/$S/hold_mimo
log "unheld; trials start ($(cat build/$S/VERSION))"
setsid nohup python3 build/trial.py $S --models deepseek --no-verdict --first-run 1 --max-runs 3 > build/$S/trial_ds_chain.log 2>&1 < /dev/null &
sleep 15
setsid nohup python3 build/trial.py $S --models mimo --no-verdict --first-run 1 --max-runs 3 > build/$S/trial_mimo_chain.log 2>&1 < /dev/null &
log "trials launched"
