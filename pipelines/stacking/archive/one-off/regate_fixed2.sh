#!/bin/bash
# Re-gate the 2 fixed defect tasks AFTER the 6 no-network batch drains (avoid pile-on with trials).
R="$HOME/cwe-bench"; cd "$R" || exit 1
SLUGS="stk-kyverno-ghsacvq5 stk-langflow-794"
LOG="$R/stacking/out/queue/regate-fixed2.log"
log(){ echo "$(date -u +%FT%TZ) FIXED2 $*" | tee -a "$LOG"; }
log "waiting for the 6 no-network re-gate batch to finish before starting"
# wait until no regate.sh jobs are running (the 6-batch drained) and the batch driver is gone
while [ "$(pgrep -fc '[r]egate.sh')" -gt 0 ] || [ "$(pgrep -c '[r]egate_batch.sh')" -gt 0 ]; do sleep 60; done
log "6-batch done; starting kyverno + langflow re-gate (max 2 concurrent, container cap 50)"
MAXJOBS=2; CAP=50
for s in $SLUGS; do
  while :; do
    run=$(pgrep -fc "[r]egate.sh"); cc=$(timeout 15 docker ps -q | wc -l)
    [ "$run" -lt "$MAXJOBS" ] && [ "$cc" -lt "$CAP" ] && break
    sleep 20
  done
  setsid nohup bash stacking/regate.sh "$s" >/dev/null 2>&1 < /dev/null &
  log "launched $s (running regates=$(pgrep -fc '[r]egate.sh'), containers=$(timeout 15 docker ps -q|wc -l))"
  sleep 25
done
while [ "$(pgrep -fc '[r]egate.sh')" -gt 0 ]; do sleep 20; done
log "done. outcomes:"
for s in $SLUGS; do echo "  $s: $(grep -E 'REGATE (SOUND|STOP)' build/$s/stack_pipeline.log 2>/dev/null|tail -1|sed 's/.*REGATE //')" | tee -a "$LOG"; done
