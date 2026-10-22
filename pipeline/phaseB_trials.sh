#!/bin/bash
# Phase B: rolling trials (UP TO 16 concurrent) of the 31 hardened candidates.
# Both models, early-abort on solve, CWE_AGENT_TIMEOUT_MULT=1.5. Idempotent via markers.
# Driven by xargs -P16 = true rolling queue (as one task finishes, the next starts).
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/phaseB_trials.log
PAR="${PHASEB_PAR:-16}"
CANDS="langchain-ds prompty-ds new-api-ds whistle-ds gogs-ds limesurvey-ds vitest-ds grav-ds compliance-trestle-ds ghost-ds airflow-ds airflow-info-exposure-inj arc-ds astro-ds backstage-ds ckan-mcp-server-ds coreutils-ds django-cms-ds fission-ds flyto-core-ds hazelcast-ds jetty.project-ds keras-ds n8n-ds orval-ds pimcore-ds portainer-ds rsdoctor-ds surrealdb-ds typo3-ds vibe-trading-ds"
echo "=== PHASE B launch $(date -u +%FT%TZ): $(echo $CANDS|wc -w) candidates, rolling P=$PAR (both models, early-abort, MULT=1.5) ===" >> "$LOG"
printf '%s\n' $CANDS | xargs -P "$PAR" -I '{}' bash -c '
  s="$1"; LOG="build/pipeline/phaseB_trials.log"; cd "$HOME/cwe-bench" || exit 0
  [ -f build/$s/.sound ] || { echo "[skip $s] not sound" >> "$LOG"; exit 0; }
  { [ -f build/$s/.auto_trialed ] || [ -f build/$s/.terminal ]; } && { echo "[skip $s] already trialed/terminal" >> "$LOG"; exit 0; }
  if [ -f build/$s/.trial_running ]; then
    pgrep -f "[b]uild/trial\.py $s( |\$)" >/dev/null && { echo "[skip $s] trial already live" >> "$LOG"; exit 0; }
    echo "[relaunch $s] stale .trial_running" >> "$LOG"
  fi
  touch build/$s/.trial_running
  sleep $((RANDOM%45))   # ease cold-fill container burst (VM stagger rule)
  echo "[trial-start $s $(date -u +%T)]" >> "$LOG"
  CWE_AGENT_TIMEOUT_MULT=1.5 python3 build/trial.py "$s" >> "build/$s/auto_trial.out" 2>&1; rc=$?
  verdict=$(grep "^\[trial\] $s: " "build/$s/auto_trial.out" | tail -1)
  ds=$(python3 pipeline/trial_state.py "$s" deepseek 2>/dev/null); mm=$(python3 pipeline/trial_state.py "$s" mimo 2>/dev/null)
  if [ $rc -eq 0 ]; then touch "build/$s/.auto_trialed"; what=complete
  else what="INCOMPLETE (exit $rc; re-queued)"; fi
  rm -f "build/$s/.trial_running"
  echo "[trial-done $s $(date -u +%T)] $what | ds: $ds | mm: $mm | ${verdict#*: }" >> "$LOG"
' _ '{}'
echo "=== PHASE B all slots drained $(date -u +%FT%TZ) ===" >> "$LOG"
touch build/pipeline/phaseB.done
