#!/bin/bash
# Firmly stop the original DS lane + its gate/trial children, detached-safe.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
{
echo "=== stop_lane START $(date -u +%FT%TZ) ==="
pkill -9 -f "run_lane.sh deepseek"
pkill -9 -f "run_pipeline.sh deepseek"
pkill -9 -f "common/gate/gate.py"
pkill -9 -f "common/trial/trial.py"
sleep 6
echo "after kill: run_lane=$(pgrep -fc run_lane.sh) run_pipeline=$(pgrep -fc 'run_pipeline.sh') gate.py=$(pgrep -fc gate.py) trial.py=$(pgrep -fc trial.py)"
docker ps -q | xargs -r docker rm -f >/dev/null 2>&1
echo "containers running=$(docker ps -q | wc -l)"
echo "=== stop_lane DONE $(date -u +%FT%TZ) ==="
} >> build/pipeline/stop_lane.log 2>&1
