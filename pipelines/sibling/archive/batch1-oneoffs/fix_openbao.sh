#!/bin/bash
# openbao-ds was stalled by a gate nop compose-flake (image + authoring already done).
# Clear stale lock/containers and RE-GATE under the raised timeouts. Detached-safe.
cd "$HOME/cwe-bench" || exit 1
export COMPOSE_HTTP_TIMEOUT=300 DOCKER_CLIENT_TIMEOUT=300
LOG=build/pipeline/fix_openbao.log
{
echo "=== fix_openbao START $(date -u +%FT%TZ) ==="
# stale throwaway containers (images kept)
docker ps -a --format '{{.Names}}' | grep -E '^openbao-ds__' | xargs -r docker rm -f >/dev/null 2>&1
# stale state that blocks a clean gate
rm -rf build/openbao-ds/.lockdir build/openbao-ds/gate_report.partial.json
echo "task-tree files: $(find tasks/openbao-ds -type f 2>/dev/null | wc -l) | image present: $(docker images -q 'openbao-ds__*-main' | head -1 | wc -l)"
echo "re-gating openbao-ds ..."
bash pipeline/gate_one_ds.sh openbao-ds
mk=$( [ -f build/openbao-ds/.sound ] && echo SOUND || ([ -f build/openbao-ds/.unsound ] && echo unsound || echo no-marker) )
echo "=== fix_openbao DONE $(date -u +%FT%TZ) verdict=$mk ==="
} >> "$LOG" 2>&1
