#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-kyverno-ghsacvq5; c=$s-control
ff() { FAIRFIX_BRIEF="build/$1/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$1" >> "build/$1/ride_along.log" 2>&1; }
log "$s: fairfix (keep instruction; Namespace object refused; tests+reference+check patch), control first"
ff "$c" & pc=$!; sleep 60; ff "$s"; rs=$?; wait $pc; rc=$?
log "$s fairfix rc=$rs ($(cat build/$s/fairfix_status.txt)); control rc=$rc ($(cat build/$c/fairfix_status.txt))"
[ "$rs" = 0 ] && [ "$rc" = 0 ] || exit 1
bash pipeline/gate_one_ds.sh "$c" >> "build/$c/ride_along.log" 2>&1; gc=$?
bash pipeline/gate_one_ds.sh "$s" >> "build/$s/ride_along.log" 2>&1; gs=$?
log "$s container gate rc=$gs; control rc=$gc; listing: $(python3 -I stacking/listing_verdict.py $s | head -1)"
[ "$gs" = 0 ] || exit 1
for x in "$s" "$c"; do [ -f "build/$x/.sound" ] || continue; for m in deepseek mimo; do
  setsid nohup python3 build/trial.py "$x" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/kyverno-retrial-$x-$m.log" 2>&1 < /dev/null &
  sleep $((15 + RANDOM % 15)); done; done
log "$s: re-trials launched (task+control) on version $(cat build/$s/VERSION)"
