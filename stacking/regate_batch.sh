#!/bin/bash
# Rolling re-gate of the no-network tasks: max 3 concurrent regate.sh, hold if containers near the cap.
R="$HOME/cwe-bench"; cd "$R" || exit 1
SLUGS="stk-comfyui-manager-2366 stk-jsonpath-ghsahw8r stk-lobe-chat-ghsa3fc8 stk-nova-ghsaxc4g stk-nuclei-ghsajpvm stk-senaite-core-4280"
LOG="$R/stacking/out/queue/regate-batch.log"
log(){ echo "$(date -u +%FT%TZ) BATCH $*" | tee -a "$LOG"; }
MAXJOBS=3; CAP=52
log "start: 6 no-network re-gates, max $MAXJOBS concurrent, container cap $CAP"
for s in $SLUGS; do
  # wait for a free slot and container headroom
  while :; do
    run=$(pgrep -fc "[r]egate.sh")
    cc=$(timeout 15 docker ps -q | wc -l)
    [ "$run" -lt "$MAXJOBS" ] && [ "$cc" -lt "$CAP" ] && break
    sleep 20
  done
  setsid nohup bash stacking/regate.sh "$s" >/dev/null 2>&1 &
  log "launched $s (running regates=$(pgrep -fc '[r]egate.sh'), containers=$(timeout 15 docker ps -q|wc -l))"
  sleep 25
done
# wait for all to finish
while [ "$(pgrep -fc '[r]egate.sh')" -gt 0 ]; do sleep 20; done
log "done. SOUND now (non-control)=$(ls build/stk-*/.sound 2>/dev/null|grep -v control|wc -l)"
for s in $SLUGS; do echo "  $s: $(grep -E 'REGATE (SOUND|STOP)' build/$s/stack_pipeline.log 2>/dev/null | tail -1)"; done | tee -a "$LOG"
