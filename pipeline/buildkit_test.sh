#!/bin/bash
# Validate the BuildKit-off fix on a SOUND task (trivy-ds) under live concurrency.
# gate_one_ds.sh sources docker-tuning.env, so the gate runs with DOCKER_BUILDKIT=0.
# With buildkit off, trivy's compose opens no session -> should be immune to the
# "only one connection allowed" collisions even while other buildkit-ON gates run.
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/buildkit_test.log
{
echo "=== buildkit_test trivy-ds START $(date -u +%FT%TZ) ==="
. pipeline/docker-tuning.env 2>/dev/null
echo "env: DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-unset} COMPOSE_DOCKER_CLI_BUILD=${COMPOSE_DOCKER_CLI_BUILD:-unset}"
rm -f build/trivy-ds/.sound build/trivy-ds/.unsound build/trivy-ds/.lockdir 2>/dev/null
rm -rf build/trivy-ds/.lockdir 2>/dev/null
: > build/trivy-ds/gate_test.log
bash pipeline/gate_one_ds.sh trivy-ds > build/trivy-ds/gate_test.log 2>&1
mk=$( [ -f build/trivy-ds/.sound ] && echo SOUND || ([ -f build/trivy-ds/.unsound ] && echo unsound || echo none) )
echo "RESULT marker=$mk"
echo "compose-command-failed lines this run: $(grep -c 'compose command failed' build/trivy-ds/gate_test.log)"
echo "only-one-connection lines this run:    $(grep -c 'only one connection' build/trivy-ds/gate_test.log)"
echo "stages: $(grep -oE 'nop=[A-Za-z]+|oracle=[A-Za-z]+|patches=[A-Za-z]+' build/trivy-ds/gate_test.log | paste -sd' ' -)"
echo "=== buildkit_test DONE $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
