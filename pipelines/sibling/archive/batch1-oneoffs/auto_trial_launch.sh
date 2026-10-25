#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/auto_trial.log
touch build/litellm-ds/.terminal   # confirmed both-model breaker -> do not trial
CANDS="airflow-ds arc-ds backstage-ds ckan-mcp-server-ds compliance-trestle-ds django-cms-ds ec2-fleet-plugin-ds electron-builder-ds flowise-ds ghost-ds gogs-ds grav-ds hazelcast-ds hermes-agent-ds hubuum-client-rust-ds jetty.project-ds langchain-ds limesurvey-ds mcp-atlassian-ds mockoon-ds n8n-ds new-api-ds pimcore-ds prompty-ds protobuf.js-ds rsdoctor-ds seaweedfs-ds siyuan-ds surrealdb-ds theia-ds traefik-ds typo3-ds vitest-ds whistle-ds"
echo "=== auto_trial launch $(date -u +%FT%TZ): up to $(echo $CANDS|wc -w) trials (both models, early-abort, 3h) ===" >> "$LOG"
# Markers: .trial_running while a trial is in flight (a second launch skips it); .auto_trialed
# only once trial.py reports a COMPLETE result (exit 0). An incomplete trial (infrastructure kept
# it from 3 graded runs: exit 2) is re-queued, never parked for good. Until 2026-10-20
# .auto_trialed was written before the trial started, so one compose burst parked
# flowise-ds / hubuum-client-rust-ds permanently.
n=0
for s in $CANDS; do
  [ -f build/$s/.sound ] || continue
  { [ -f build/$s/.auto_trialed ] || [ -f build/$s/.terminal ]; } && continue
  if [ -f build/$s/.trial_running ]; then
    pgrep -f "[b]uild/trial\.py $s( |\$)" >/dev/null && continue
    echo "  $s: stale .trial_running (no trial.py process) -> relaunching" >> "$LOG"
  fi
  touch build/$s/.trial_running
  setsid bash -c '
    s=$1; LOG=$2; sleep $((RANDOM%30)); cd "$HOME/cwe-bench"
    CWE_AGENT_TIMEOUT_MULT=1.5 python3 build/trial.py "$s" >> "build/$s/auto_trial.out" 2>&1; rc=$?
    verdict=$(grep "^\[trial\] $s: " "build/$s/auto_trial.out" | tail -1)
    ds=$(python3 pipeline/trial_state.py "$s" deepseek); mm=$(python3 pipeline/trial_state.py "$s" mimo)
    if [ $rc -eq 0 ]; then touch "build/$s/.auto_trialed"; what=complete
    else what="INCOMPLETE (trial.py exit $rc; re-queued, not a verdict)"; fi
    rm -f "build/$s/.trial_running"
    echo "[trial-done $s $(date -u +%T)] $what | ds: $ds | mm: $mm | ${verdict#*: }" >> "$LOG"
  ' _ "$s" "$LOG" >/dev/null 2>&1 < /dev/null &
  n=$((n+1))
done
echo "launched $n trials $(date -u +%FT%TZ)" >> "$LOG"
