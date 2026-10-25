#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-comfyui-manager-2366; c=$s-control
log "$s: fairfix (restore the carry-over contracts the upgrade removed)"
FAIRFIX_BRIEF="build/$s/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$s" >> "build/$s/ride_along.log" 2>&1; rc=$?
log "$s fairfix rc=$rc ($(cat build/$s/fairfix_status.txt)); control same instruction: $(cmp -s tasks/$s/instruction.md tasks/$c/instruction.md && echo yes || echo NO); listing: $(python3 -I stacking/listing_verdict.py $s | head -1)"
[ "$rc" = 0 ] || exit 1
python3 -I stacking/listing_verdict.py "$s" > /dev/null; [ $? = 0 ] || { log "$s: listing check FAILs after the fix; trials NOT started"; exit 1; }
for x in "$s" "$c"; do for m in deepseek mimo; do
  setsid nohup python3 build/trial.py "$x" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/comfyui-extra-$x-$m.log" 2>&1 < /dev/null &
  sleep $((15 + RANDOM % 20)); done; done
log "$s: fixed v3 (or later) trials launched for task + control (4 jobs)"
