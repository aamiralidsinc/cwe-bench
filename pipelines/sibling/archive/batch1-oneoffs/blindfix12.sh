#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/blindfix12.log
TW="astro-ds composer-ds coreutils-ds flyto-core-ds keras-ds knowns-ds openbao-ds orval-ds tinacms-ds trivy-ds vibe-trading-ds yamcs-ds"
{
echo "=== blindfix 12 START $(date -u +%FT%TZ) C=3 staggered (generate blind.patch -> re-gate) ==="
printf '%s\n' $TW | xargs -P3 -I{} bash -c 'sleep $((RANDOM%30)); cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_blindfix.sh "$1" >> "build/$1/blindfix.nohup" 2>&1; bash pipeline/gate_one_ds.sh "$1" >> "build/$1/blindfix.nohup" 2>&1; echo "[blindfix+gate $1] $([ -f build/$1/.sound ] && echo SOUND || echo unsound) blind.patch:$([ -f build/$1/checks/blind.patch ] && echo yes || echo MISSING)"' _ {}
echo "=== blindfix 12 DONE $(date -u +%FT%TZ) ==="
echo BLINDFIX12-DONE
} >> "$LOG" 2>&1
