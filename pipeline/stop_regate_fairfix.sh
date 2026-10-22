#!/bin/bash
# Stop the futile blind.patch-blocked re-gate; launch fairfix on the 8 confirmed-unfair tasks.
# Does NOT touch containers (litellm r6 trial is still running and must be protected).
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/stop_regate_fairfix.log
{
echo "=== stop regate + launch fairfix $(date -u +%FT%TZ) ==="
pkill -9 -f "[r]egate_all_ds"; pkill -9 -f "[g]ate_one_ds"; pkill -9 -f "[b]uilder/gate.py"
sleep 5
echo "regate stopped: regate=$(pgrep -cf '[r]egate_all_ds') gate_one=$(pgrep -cf '[g]ate_one_ds') gate.py=$(pgrep -cf '[b]uilder/gate.py')"
echo "litellm trial still alive? $(pgrep -cf '[t]rial.py litellm') (must be >=1)"
TASKS="protobuf.js-ds airflow-ds hazelcast-ds hermes-agent-ds siyuan-ds flowise-cross-tenant-inj prompty-path-read-inj vitest-api-fs-authz-inj"
echo "launching fairfix P4 on: $TASKS"
printf '%s\n' $TASKS | xargs -P4 -I{} bash -c 'cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_fairfix.sh "$1" >> "build/$1/fairfix.nohup" 2>&1; echo "[done $1] fairfix-exit=$(cat build/$1/fairfix-exit.txt 2>/dev/null)" >> build/pipeline/stop_regate_fairfix.log' _ {}
echo "=== fairfix batch DONE $(date -u +%FT%TZ) ==="
echo ALL-FAIRFIX-DONE
} >> "$LOG" 2>&1
