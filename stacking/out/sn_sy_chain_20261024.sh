#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
senaite() { local s=stk-senaite-core-4280
  bash pipeline/gate_one_ds.sh "$s" >> "build/$s/testfix-20261024/gate.log" 2>&1; local gs=$?
  log "$s gate after record-parsing test fix rc=$gs (0 = sound)"; [ "$gs" = 0 ] || return
  rm -f build/$s/hold_mimo
  setsid nohup python3 build/trial.py "$s" --models mimo --no-verdict --first-run 2 --max-runs 3 > stacking/out/queue/senaite-mimo-fresh.log 2>&1 < /dev/null &
  log "$s: MiMo unheld; fresh MiMo runs launched (r1 was test-fault)"; }
siyuan() { local s=stk-siyuan-ghsa4mx9 c=stk-siyuan-ghsa4mx9-control
  log "$s: second repair fairfix (icon test + foreignObject checker; keep instruction)"
  FAIRFIX_BRIEF="build/$s/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$s" >> "build/$s/ride_along.log" 2>&1; local rc=$?
  log "$s fairfix rc=$rc ($(cat build/$s/fairfix_status.txt))"; [ "$rc" = 0 ] || return
  bash pipeline/gate_one_ds.sh "$s" >> "build/$s/ride_along.log" 2>&1; local gs=$?
  log "$s container gate rc=$gs; listing: $(python3 -I stacking/listing_verdict.py $s | head -1)"; [ "$gs" = 0 ] || return
  rm -f build/$s/hold_* build/$c/hold_*
  for m in deepseek mimo; do setsid nohup python3 build/trial.py "$s" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/siyuan-r2-$m.log" 2>&1 < /dev/null & sleep 20; done
  log "$s: unheld; re-trials launched on version $(cat build/$s/VERSION) (control unchanged, keeps its runs)"; }
senaite & sleep 30; siyuan; wait
