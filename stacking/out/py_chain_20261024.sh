#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-pyload-ghsa4744
log "$s: fairfix (startup test checks the effective folder, not the saved file)"
FAIRFIX_BRIEF="build/$s/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$s" >> "build/$s/ride_along.log" 2>&1; rc=$?
log "$s fairfix rc=$rc ($(cat build/$s/fairfix_status.txt))"; [ "$rc" = 0 ] || exit 1
bash pipeline/gate_one_ds.sh "$s" >> "build/$s/ride_along.log" 2>&1; gs=$?
log "$s container gate rc=$gs; listing: $(python3 -I stacking/listing_verdict.py $s | head -1)"; [ "$gs" = 0 ] || exit 1
rm -f build/$s/hold_deepseek build/$s/hold_mimo
for m in deepseek mimo; do setsid nohup python3 build/trial.py "$s" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/pyload4744-retrial-$m.log" 2>&1 < /dev/null & sleep 20; done
log "$s: unheld; re-trials launched on version $(cat build/$s/VERSION)"
