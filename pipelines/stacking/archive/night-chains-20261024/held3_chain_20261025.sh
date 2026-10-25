#!/bin/bash
# User decision 2026-10-25: comfyui + pyload-7gvf accept wording (A); fabio reword X-Real-Ip then A. Trial all + controls.
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/held3_chain.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
trials() { local x=$1; rm -f build/$x/hold_deepseek build/$x/hold_mimo
  setsid nohup python3 build/trial.py $x --models deepseek --no-verdict --first-run 1 --max-runs 3 > build/$x/trial_ds_held3.log 2>&1 < /dev/null &
  sleep $((40 + RANDOM % 30))
  setsid nohup python3 build/trial.py $x --models mimo --no-verdict --first-run 1 --max-runs 3 > build/$x/trial_mimo_held3.log 2>&1 < /dev/null &
  sleep $((40 + RANDOM % 30)); log "$x: unheld, trials launched ($(cat build/$x/VERSION))"; }
pyload() { trials stk-pyload-ghsa7gvf; trials stk-pyload-ghsa7gvf-control; }
comfy() { local c=stk-comfyui-manager-2366-control
  bash pipeline/gate_one_ds.sh $c >> build/$c/held3_chain.log 2>&1; local g=$?; log "$c gate rc=$g (0 = sound)"
  trials stk-comfyui-manager-2366; [ $g = 0 ] && trials $c || log "$c not sound: control not trialled"; }
fabio() { local s=stk-fabio-ghsafq95
  FAIRFIX_BRIEF=build/$s/AUDIT-FIX-20261025.md ./drive.sh deepseek bash stacking/run_fairfix_stack.sh $s >> build/$s/held3_chain.log 2>&1; local rc=$?
  log "$s fairfix (reword X-Real-Ip) rc=$rc ($(cat build/$s/fairfix_status.txt)); listing: $(python3 -I stacking/listing_verdict.py $s | head -1)"
  [ $rc = 0 ] || { log "$s chain stopped (held)"; return; }
  grep -q "X-Real-Ip" tasks/$s/instruction.md && { log "$s: X-Real-Ip still in instruction; chain stopped (held)"; return; }
  bash pipeline/gate_one_ds.sh $s >> build/$s/held3_chain.log 2>&1; local g=$?
  bash pipeline/gate_one_ds.sh $s-control >> build/$s/held3_chain.log 2>&1; local gc=$?
  log "$s gate rc=$g control rc=$gc"
  [ $g = 0 ] && trials $s; [ $gc = 0 ] && trials $s-control; }
log "=== held-3 chain start"
pyload & sleep 20; comfy & sleep 20; fabio & wait
log "=== held-3 chain done"
