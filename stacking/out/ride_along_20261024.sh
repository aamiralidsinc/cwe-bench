#!/bin/bash
# Ride-along steps for 2026-10-24 (everything except trials; trials run separately afterwards):
#   avideo-ghsaghcv : audit fix (harness stub) on the control, then the task -> container gate both -> upgrade
#   siyuan          : audit fix (serve fixture)                         -> container gate        -> upgrade
#   kyverno, langflow, senaite : paused re-gates (task + control)       -> upgrade
# A step that fails stops that task's chain; the others continue. Progress: stacking/out/ride_along.log
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/ride_along.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
gate() { bash pipeline/gate_one_ds.sh "$1" >> "build/$1/ride_along.log" 2>&1; }
fairfix() { FAIRFIX_BRIEF="build/$1/AUDIT-FIX-20261024.md" ./drive.sh deepseek bash stacking/run_fairfix_stack.sh "$1" >> "build/$1/ride_along.log" 2>&1; }
upgrade() { ./drive.sh deepseek bash stacking/run_upgrade_stack.sh "$1" >> "build/$1/ride_along.log" 2>&1; local rc=$?; log "$1 upgrade rc=$rc: $(cat "build/$1/upgrade_stack_status.txt" 2>/dev/null)"; return $rc; }

avideo() {
  local s=stk-avideo-ghsaghcv c=stk-avideo-ghsaghcv-control
  log "$s: audit fix on the control, then the task"
  fairfix "$c" & local pc=$!; sleep 60
  fairfix "$s"; local rs=$?; wait "$pc"; local rc=$?
  log "$s fairfix rc=$rs ($(cat build/$s/fairfix_status.txt)); control rc=$rc ($(cat build/$c/fairfix_status.txt))"
  [ "$rs" = 0 ] && [ "$rc" = 0 ] || { log "$s: audit fix did not finish; chain stopped"; return; }
  gate "$c"; local gc=$?; gate "$s"; local gs=$?
  log "$s container gate rc=$gs; control rc=$gc (0 = sound)"
  [ "$gs" = 0 ] || { log "$s: gate not sound after the fix; chain stopped"; return; }
  upgrade "$s"
}
siyuan() {
  local s=stk-siyuan-ghsa4mx9
  log "$s: audit fix (serve fixture)"
  fairfix "$s"; local rs=$?
  log "$s fairfix rc=$rs ($(cat build/$s/fairfix_status.txt))"
  [ "$rs" = 0 ] || { log "$s: audit fix did not finish; chain stopped"; return; }
  gate "$s"; local gs=$?
  log "$s container gate rc=$gs (0 = sound)"
  [ "$gs" = 0 ] || { log "$s: gate not sound after the fix; chain stopped"; return; }
  upgrade "$s"
}
regate() {
  local s=$1 c=$1-control
  log "$s: paused re-gate (task, then control)"
  gate "$s"; local gs=$?; gate "$c"; local gc=$?
  log "$s container gate rc=$gs; control rc=$gc (0 = sound)"
  [ "$gs" = 0 ] || { log "$s: gate not sound; chain stopped"; return; }
  upgrade "$s"
}

log "=== ride-along start ==="
avideo & sleep $((5 + RANDOM % 16))
siyuan & sleep $((5 + RANDOM % 16))
regate stk-kyverno-ghsacvq5 & sleep $((5 + RANDOM % 16))
regate stk-langflow-794 & sleep $((5 + RANDOM % 16))
regate stk-senaite-core-4280 &
wait
log "=== ride-along done ==="
