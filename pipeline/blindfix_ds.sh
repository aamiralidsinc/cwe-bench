#!/bin/bash
# blindfix_ds.sh <slug>... : regenerate blind.patch on the DeepSeek driver, 3 at a time, staggered.
# One line per task in the log when it ends; read build/<slug>/blindfix.log for progress.
cd "$HOME/cwe-bench" || exit 1
L=build/pipeline/blindfix_ds-$(date -u +%Y%m%dT%H%M%SZ).log; mkdir -p build/pipeline
echo "=== blind START $(date -u +%FT%TZ) driver=deepseek tasks: $* ===" >> "$L"
one() {
  sleep $((RANDOM % 20)); cd "$HOME/cwe-bench" || return
  ./drive.sh deepseek bash run_blindfix.sh "$1" >> "build/$1/blindfix.nohup" 2>&1
  echo "[blind $1] exit=$? status=$(cat "build/$1/blind_status.txt") $(date -u +%T)" >> "$2"
}
export -f one
printf "%s\n" "$@" | xargs -P3 -I{} bash -c "one {} $L"
echo "=== blind DONE $(date -u +%FT%TZ) ===" >> "$L"
