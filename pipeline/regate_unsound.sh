#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/regate_unsound.log
UNS="fission-ds ghost-ds hubuum-client-rust-ds langchain-ds new-api-ds portainer-ds prompty-ds summarize-ds"
{
echo "=== re-gate unsound START $(date -u +%FT%TZ) C=4 staggered (patched harbor) ==="
printf '%s\n' $UNS | xargs -P4 -I{} bash -c 'sleep $((RANDOM%20)); bash pipeline/gate_one_ds.sh "$1"' _ {}
for s in $UNS; do echo "  $s: $([ -f build/$s/.sound ] && echo SOUND || echo unsound)"; done
echo REGATE-UNSOUND-DONE
} >> "$LOG" 2>&1
