#!/bin/bash
# Run the stacking upgrade (stacking/run_upgrade_stack.sh) over a list of stk- slugs, N at a time,
# each start 5-20 s after the previous one. Trials are NOT started here: run them afterwards with
# stacking/stk_queue.py trial (it re-trials every .sound stk- task whose new version has no runs).
#   bash stacking/upgrade_stack_batch.sh SLUGS_FILE [N=6]
# Progress: stacking/out/upgrade_batch.log (one line per start and finish, then a summary).
set -uo pipefail
F=${1:?usage: upgrade_stack_batch.sh SLUGS_FILE [N]}; N=${2:-6}
R="$HOME/cwe-bench"; cd "$R" || exit 1
LOG=stacking/out/upgrade_batch.log
echo "$(date -u +%FT%TZ) batch start: $(grep -c . "$F") tasks, $N at a time" >> "$LOG"
grep -v '^\s*#' "$F" | grep . | while read -r s; do echo "$s"; done | xargs -P "$N" -I{} bash -c '
  sleep $((5 + RANDOM % 16)); cd "$HOME/cwe-bench"
  echo "$(date -u +%FT%TZ) [start] $1" >> stacking/out/upgrade_batch.log
  ./drive.sh deepseek bash stacking/run_upgrade_stack.sh "$1" >> "build/$1/upgrade_stack.nohup" 2>&1; rc=$?
  echo "$(date -u +%FT%TZ) [finish] $1 rc=$rc $(cat build/$1/upgrade_stack_status.txt 2>/dev/null)" >> stacking/out/upgrade_batch.log' _ {}
echo "$(date -u +%FT%TZ) batch done: $(grep -c "\[finish\].* rc=0 " "$LOG") upgraded with listing PASS (cumulative in this log)" >> "$LOG"
