#!/bin/bash
# MiMo-gap pass (run NOW alongside surrealdb's live trial): MiMo-only trial over the 21
# DeepSeek-solved tasks that early-aborted before MiMo, so every task gets a MiMo verdict
# (captures single-model MiMo breakers). Rolling xargs -P; skip-guards protect surrealdb
# (live) and any already-mimo-complete task from a double-run. Budget: P=14 + surrealdb(1) <=16.
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/phaseB_mimo.log
PAR="${MIMO_PAR:-14}"
CANDS="langchain-ds prompty-ds new-api-ds whistle-ds gogs-ds limesurvey-ds vitest-ds compliance-trestle-ds ghost-ds airflow-info-exposure-inj arc-ds astro-ds ckan-mcp-server-ds coreutils-ds fission-ds hazelcast-ds n8n-ds orval-ds pimcore-ds rsdoctor-ds vibe-trading-ds"
echo "=== MIMO-GAP pass launch $(date -u +%FT%TZ): $(echo $CANDS|wc -w) cands, rolling P=$PAR (concurrent with surrealdb live) ===" >> "$LOG"
printf '%s\n' $CANDS | xargs -P "$PAR" -I '{}' bash -c '
  s="$1"; LOG="build/pipeline/phaseB_mimo.log"; cd "$HOME/cwe-bench" || exit 0
  [ -f build/$s/.sound ] || { echo "[skip $s] not sound" >> "$LOG"; exit 0; }
  st=$(python3 pipeline/trial_state.py "$s" mimo 2>/dev/null); rc=$?
  [ $rc -eq 0 ] && { echo "[skip $s] mimo already complete: $st" >> "$LOG"; exit 0; }
  [ $rc -eq 3 ] && { echo "[STUCK $s] mimo: $st -> needs a person" >> "$LOG"; exit 0; }
  pgrep -f "[b]uild/trial\.py $s( |\$)" >/dev/null && { echo "[skip $s] trial live" >> "$LOG"; exit 0; }
  sleep $((RANDOM%45))
  echo "[mimo-start $s $(date -u +%T)]" >> "$LOG"
  CWE_AGENT_TIMEOUT_MULT=1.5 python3 build/trial.py "$s" --models mimo --no-verdict >> "build/$s/auto_trial_mimo.out" 2>&1; r=$?
  mm=$(python3 pipeline/trial_state.py "$s" mimo 2>/dev/null)
  echo "[mimo-done $s $(date -u +%T)] exit=$r | mm: $mm" >> "$LOG"
' _ '{}'
echo "=== MIMO-GAP pass drained $(date -u +%FT%TZ) ===" >> "$LOG"
touch build/pipeline/phaseB_mimo.done
