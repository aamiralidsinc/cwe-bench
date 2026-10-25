#!/bin/bash
# Launch read-only fairness reviews (DeepSeek, NO Docker) for the stacking breaker candidates, in parallel.
R="$HOME/cwe-bench"; cd "$R" || exit 1
SLUGS="stk-avideo-ghsaghcv stk-filebrowser-ghsa8wc8 stk-dagu-ghsaph8x stk-mjml-ghsa45h5 stk-siyuan-ghsa4mx9 stk-tensorflow-ghsajjr8"
mkdir -p stacking/out/fairness
LOG="$R/stacking/out/fairness/launch.log"
log(){ echo "$(date -u +%FT%TZ) FAIRNESS $*" | tee -a "$LOG"; }
log "launching fairness on 6 candidates (read-only, no Docker)"
for s in $SLUGS; do
  [ -f "build/$s/.sound" ] || { log "SKIP $s (not sound)"; continue; }
  setsid nohup ./drive.sh deepseek bash stacking/run_fairness_stack.sh "$s" \
     >> "stacking/out/fairness/$s.log" 2>&1 </dev/null &
  log "launched $s (pid=$!)"
  sleep 8
done
log "all launched; verdicts via pipeline/fairness_verdict.py <slug> when FAIRNESS.md lands (timeout 2400s/40min each)"
