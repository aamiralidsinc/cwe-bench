#!/bin/bash
# orchestrator_tick.sh [deepseek|claude] [every_min] [model] : run the scale-run orchestrator (pipelines/router/ORCHESTRATOR.md)
# as one fresh headless session per tick, every <every_min> minutes (default 30). Run it on the VM:
#
#   setsid nohup bash pipelines/router/orchestrator_tick.sh deepseek > /dev/null 2>&1 < /dev/null &   # DeepSeek V4.1 Flash
#   setsid nohup bash pipelines/router/orchestrator_tick.sh claude 30 claude-opus-5-5 > /dev/null 2>&1 < /dev/null &
#
# Only one orchestrator may run at a time (a lock file guards it); stop the loop by its PID, never by pattern.
# The prompt on the command line is one short sentence, so process listings never show pipeline script names from
# the orchestrator's own arguments (status checks match those names). Each tick's output: out/orchestrator/ticks/.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
DRV=${1:-deepseek}; EV=${2:-30}; O=pipelines/router/out/orchestrator; mkdir -p "$O/ticks"
exec 9> "$O/.lock"; flock -n 9 || { echo "another orchestrator is running (lock $O/.lock)"; exit 1; }
P="You are the scale-run orchestrator. Read pipelines/router/ORCHESTRATOR.md in full, then carry out exactly one tick as it describes and stop."
while true; do
  T=$(date -u +%Y%m%dT%H%M%SZ); start=$(date +%s)
  case "$DRV" in
    deepseek) pre=("$CWE_DRIVE" deepseek) ;;          # drive.sh exports MODEL and the DeepSeek endpoint
    claude)   pre=(env MODEL="${3:-claude-opus-5-5}") ;;
    *) echo "usage: orchestrator_tick.sh [deepseek|claude] [every_min] [model]"; exit 2 ;;
  esac
  # 50 min cap per tick: a tick waits for its auditors; a longer one is cut and the next tick picks up from the journal.
  "${pre[@]}" bash -c 'timeout 3000 "$HOME/.local/bin/claude" -p "$0" --model "$MODEL" --permission-mode bypassPermissions \
      --add-dir "$HOME/.tb-graders/cwe" --output-format json' "$P" > "$O/ticks/$T.json" 2> "$O/ticks/$T.err"
  echo "$(date -u +%FT%TZ) tick $T ($DRV) exit $? in $(( ($(date +%s) - start) / 60 )) min" >> "$O/ticks.log"
  left=$(( EV * 60 - ($(date +%s) - start) )); [ "$left" -gt 0 ] && sleep "$left"
done
