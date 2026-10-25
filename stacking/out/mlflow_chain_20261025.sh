#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
S=stk-mlflow-3745 C=$S-control L=stacking/out/mlflow_repair_chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
touch build/$S/hold_deepseek build/$S/hold_mimo build/$C/hold_deepseek build/$C/hold_mimo
log "fairfix (instruction-only scope of the destination sentence)"
FAIRFIX_BRIEF=build/$S/AUDIT-FIX-20261025.md ./drive.sh deepseek bash stacking/run_fairfix_stack.sh $S >> build/$S/mlflow_repair_chain.log 2>&1; rc=$?
log "fairfix rc=$rc ($(cat build/$S/fairfix_status.txt)); version $(cat build/$S/VERSION); listing: $(python3 -I stacking/listing_verdict.py $S | head -1)"
[ $rc = 0 ] || { log "chain stopped (held)"; exit 1; }
cmp -s tasks/$S/instruction.md tasks/$C/instruction.md || { log "control instruction differs; chain stopped"; exit 1; }
bash pipeline/gate_one_ds.sh $S >> build/$S/mlflow_repair_chain.log 2>&1; g=$?
bash pipeline/gate_one_ds.sh $C >> build/$S/mlflow_repair_chain.log 2>&1; gc=$?
log "gate task rc=$g control rc=$gc (0 = sound)"
for x in $S $C; do
  if [ -f build/$x/.sound ]; then rm -f build/$x/hold_deepseek build/$x/hold_mimo
    setsid nohup python3 build/trial.py $x --models deepseek --no-verdict --first-run 1 --max-runs 3 > build/$x/trial_ds_repair.log 2>&1 < /dev/null &
    sleep $((40 + RANDOM % 30))
    setsid nohup env CWE_AGENT_TIMEOUT_MULT=1.5 python3 build/trial.py $x --models mimo --no-verdict --first-run 1 --max-runs 3 > build/$x/trial_mimo_repair.log 2>&1 < /dev/null &
    sleep $((40 + RANDOM % 30)); log "$x: trials launched ($(cat build/$x/VERSION); MiMo at 3 h)"
  else log "$x not sound: no trials"; fi
done
