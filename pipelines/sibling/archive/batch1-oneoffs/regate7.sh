#!/bin/bash
# Stop the broad auto-regate, then re-gate EXACTLY this batch's 7 non-sound tasks,
# under the raised compose/client timeouts, at concurrency 5. Detached-safe.
cd "$HOME/cwe-bench" || exit 1
export COMPOSE_HTTP_TIMEOUT=300 DOCKER_CLIENT_TIMEOUT=300
LOG=build/pipeline/regate7.log
{
echo "=== regate7 START $(date -u +%FT%TZ) ==="
# stop the broad regate + any gate children it spawned
pkill -9 -f "regate_all_ds.sh"; pkill -9 -f "gate_one_ds.sh"; pkill -9 -f "builder/gate.py"; pkill -9 -f "build/trial.py"
sleep 5
docker ps -q | xargs -r docker rm -f >/dev/null 2>&1
echo "cleaned: containers=$(docker ps -q | wc -l)"
SEVEN="seaweedfs-ds traefik-ds rsdoctor-ds vibe-trading-ds trivy-ds yamcs-ds pimcore-ds"
echo "re-gating: $SEVEN"
printf '%s\n' $SEVEN | xargs -P 5 -I {} bash pipeline/gate_one_ds.sh {}
echo "=== regate7 DONE $(date -u +%FT%TZ) ==="
echo "--- verdicts ---"
for s in $SEVEN; do mk=$( [ -f build/$s/.sound ] && echo SOUND || ([ -f build/$s/.unsound ] && echo unsound || echo no-marker) ); echo "  $s: $mk"; done
} >> "$LOG" 2>&1
