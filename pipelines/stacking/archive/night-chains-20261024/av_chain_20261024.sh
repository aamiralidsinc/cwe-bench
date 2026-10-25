#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log; log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
s=stk-avideo-ghsaghcv
log "$s: test fix b (removed layer-forcing FuncClientTest::testServerGeneratedUiScriptRuns); gating"
bash pipeline/gate_one_ds.sh "$s" >> "build/$s/testfix-20261024b/gate.log" 2>&1; gs=$?
log "$s gate after test fix b rc=$gs (0 = sound)"
[ "$gs" = 0 ] || exit 1
bash pipeline/snapshot_experiment.sh "$s" >> "build/$s/testfix-20261024b/gate.log" 2>&1
for m in deepseek mimo; do
  setsid nohup python3 build/trial.py "$s" --models "$m" --no-verdict --first-run 1 --max-runs 3 > "stacking/out/queue/avideo-retrial-$m.log" 2>&1 < /dev/null &
  sleep $((15 + RANDOM % 15)); done
log "$s: re-trials launched (ds, mimo) on version $(cat build/$s/VERSION)"
