#!/bin/bash
# Re-gate the 8 older unsound DS tasks under the raised timeouts, C=4. Detached-safe.
cd "$HOME/cwe-bench" || exit 1
export COMPOSE_HTTP_TIMEOUT=300 DOCKER_CLIENT_TIMEOUT=300
LOG=build/pipeline/regate8.log
{
echo "=== regate8 START $(date -u +%FT%TZ) ==="
EIGHT="astro-ds coreutils-ds flyto-core-ds keras-ds knowns-ds orval-ds theia-ds tinacms-ds"
echo "re-gating: $EIGHT"
printf '%s\n' $EIGHT | xargs -P 4 -I {} bash pipeline/gate_one_ds.sh {}
echo "=== regate8 DONE $(date -u +%FT%TZ) ==="
for s in $EIGHT; do mk=$( [ -f build/$s/.sound ] && echo SOUND || ([ -f build/$s/.unsound ] && echo unsound || echo no-marker) ); echo "  $s: $mk"; done
} >> "$LOG" 2>&1
