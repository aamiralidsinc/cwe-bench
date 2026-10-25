#!/bin/bash
# reword_chain.sh SLUG : fairfix (instruction rewording brief) -> listing check -> unhold -> re-trial (task + control)
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=$1; c=$s-control
log "$s: reword fairfix start"
FAIRFIX_BRIEF="build/$s/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$s" >> "build/$s/ride_along.log" 2>&1; rc=$?
lv=$(python3 -I stacking/listing_verdict.py "$s" | head -1); python3 -I stacking/listing_verdict.py "$s" > /dev/null; lst=$?
log "$s reword fairfix rc=$rc ($(cat build/$s/fairfix_status.txt)); control same: $(cmp -s tasks/$s/instruction.md tasks/$c/instruction.md && echo yes || echo NO); listing: $lv"
[ "$rc" = 0 ] || { log "$s: fairfix did not finish; stays HELD"; exit 1; }
[ "$lst" = 0 ] || { log "$s: listing FAIL after rewording; stays HELD (needs human decision)"; exit 1; }
cmp -s tasks/$s/instruction.md tasks/$c/instruction.md || cp tasks/$s/instruction.md tasks/$c/instruction.md
python3 -I stacking/check_stack.py "$s" >> "build/$s/ride_along.log" 2>&1 || { log "$s: check_stack failed after rewording; stays HELD"; exit 1; }
rm -f build/$s/hold_deepseek build/$s/hold_mimo build/$c/hold_deepseek build/$c/hold_mimo
for x in "$s" "$c"; do [ -f "build/$x/.sound" ] || { log "$x not sound; no trial"; continue; }
  for m in deepseek mimo; do
    setsid nohup python3 build/trial.py "$x" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/reword-$x-$m.log" 2>&1 < /dev/null &
    sleep $((15 + RANDOM % 20)); done; done
log "$s: unheld; re-trials launched (task + control) on version $(cat build/$s/VERSION)"
