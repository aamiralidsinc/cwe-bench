#!/bin/bash
# Run the stacking upgrade (pipelines/stacking/5-upgrade/run_upgrade_stack.sh) over a list of stk- slugs, N at a time,
# each start 5-20 s after the previous one. Trials are NOT started here: run them afterwards with
# pipelines/stacking/6-trial/stk_queue.py trial (it re-trials every .sound stk- task whose new version has no runs).
#   bash pipelines/stacking/5-upgrade/upgrade_stack_batch.sh SLUGS_FILE [N=6]
# Progress: pipelines/stacking/out/upgrade_batch.log (one line per start and finish, then a summary).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
F=${1:?usage: upgrade_stack_batch.sh SLUGS_FILE [N]}; N=${2:-6}
R="$CWE_ROOT"; cd "$R" || exit 1
LOG=pipelines/stacking/out/upgrade_batch.log
echo "$(date -u +%FT%TZ) batch start: $(grep -c . "$F") tasks, $N at a time" >> "$LOG"
grep -v '^\s*#' "$F" | grep . | while read -r s; do echo "$s"; done | CWE_ROOT="$CWE_ROOT" xargs -P "$N" -I{} bash -c '
  sleep $((5 + RANDOM % 16)); cd "$CWE_ROOT"
  echo "$(date -u +%FT%TZ) [start] $1" >> pipelines/stacking/out/upgrade_batch.log
  common/launch/drive.sh deepseek bash pipelines/stacking/5-upgrade/run_upgrade_stack.sh "$1" >> "build/$1/upgrade_stack.nohup" 2>&1; rc=$?
  echo "$(date -u +%FT%TZ) [finish] $1 rc=$rc $(cat build/$1/upgrade_stack_status.txt 2>/dev/null)" >> pipelines/stacking/out/upgrade_batch.log' _ {}
echo "$(date -u +%FT%TZ) batch done: $(grep -c "\[finish\].* rc=0 " "$LOG") upgraded with listing PASS (cumulative in this log)" >> "$LOG"
