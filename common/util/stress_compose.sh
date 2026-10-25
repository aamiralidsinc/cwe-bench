#!/bin/bash
# Compose stress-test: fire 20 concurrent gate.py --only nop (one compose up/down each) on sound
# tasks with buildkit-off, to exceed the ~12-18 concurrent band where compose collided buildkit-ON.
# Non-destructive: --only nop does not write .sound/.unsound. Measures compose-error rate.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
. common/gate/docker-tuning.env 2>/dev/null || true
export DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0
LOG=build/pipeline/stress_compose.log
start=$(date -u +"%Y-%m-%d %H:%M:%S")
SLUGS=$(for d in build/*-ds; do [ -f "$d/.sound" ] && basename "$d"; done | head -20)
{
echo "=== compose stress START $(date -u +%FT%TZ): 20 concurrent gate.py --only nop, buildkit-off ==="
echo "tasks: $SLUGS"
printf '%s\n' $SLUGS | xargs -P20 -I{} bash -c 'python3 -I common/gate/gate.py "$1" --only nop > "build/$1/stress_nop.log" 2>&1; echo "done $1"' _ {}
echo "--- measuring ---"
ce=$(sudo journalctl -u docker --since "$start" --no-pager 2>/dev/null | grep -cE "only one connection|context deadline")
cf=$(grep -l "compose command failed" build/*-ds/stress_nop.log 2>/dev/null | wc -l)
peak=$(grep -c . <<<"$SLUGS")
echo "RESULT: concurrent gates fired=$peak | journal(only-one-connection+context-deadline) since start=$ce | tasks hitting 'compose command failed'=$cf/$peak"
echo "VERDICT: buildkit-off HOLDS if both counters ~0; FAILS if cf>0 or ce high."
echo STRESS-DONE
} >> "$LOG" 2>&1
