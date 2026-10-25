#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/upgrade_breakers.log
{
echo "=== upgrade 2 single-model breakers START $(date -u +%FT%TZ) (snapshot preserves v1 breaker) ==="
printf '%s\n' backstage-ds electron-builder-ds | xargs -P2 -I{} bash -c 'sleep $((RANDOM%10)); cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_upgrade.sh "$1" >> "build/$1/upgrade.nohup" 2>&1; echo "[upgrade done $1] $(tail -1 build/$1/upgrade-gate.log 2>/dev/null)"' _ {}
echo "=== upgrade breakers DONE $(date -u +%FT%TZ) ==="
echo UPGRADE-BREAKERS-DONE
} >> "$LOG" 2>&1
