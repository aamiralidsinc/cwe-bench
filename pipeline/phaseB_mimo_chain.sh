#!/bin/bash
# Chained MiMo pass: waits for Phase B (both-models) to FULLY drain, then runs a MiMo-only
# rolling trial over all 31 candidates so every task gets a MiMo verdict (captures single-model
# MiMo breakers that DeepSeek-solve early-abort skipped). Never stacks on a live Phase B.
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/phaseB_mimo.log
PAR="${MIMO_PAR:-16}"
CANDS="langchain-ds prompty-ds new-api-ds whistle-ds gogs-ds limesurvey-ds vitest-ds grav-ds compliance-trestle-ds ghost-ds airflow-ds airflow-info-exposure-inj arc-ds astro-ds backstage-ds ckan-mcp-server-ds coreutils-ds django-cms-ds fission-ds flyto-core-ds hazelcast-ds jetty.project-ds keras-ds n8n-ds orval-ds pimcore-ds portainer-ds rsdoctor-ds surrealdb-ds typo3-ds vibe-trading-ds"

echo "=== MIMO-CHAIN armed $(date -u +%FT%TZ): waiting for Phase B to drain ===" >> "$LOG"
# Wait for drain: phaseB.done present AND no driver AND no trial.py, confirmed twice (2x60s).
ok=0
for i in $(seq 1 720); do   # up to 12h
  d=0; [ -f build/pipeline/phaseB.done ] && d=1
  drv=$(pgrep -fc "[p]haseB_trials.sh" 2>/dev/null || echo 0)
  tp=$(pgrep -fc "[t]rial.py" 2>/dev/null || echo 0)
  if [ "$d" = 1 ] && [ "$drv" = 0 ] && [ "$tp" = 0 ]; then ok=$((ok+1)); else ok=0; fi
  [ "$ok" -ge 2 ] && break
  sleep 60
done
echo "=== MIMO-CHAIN Phase B drained $(date -u +%FT%TZ) (ok=$ok) ===" >> "$LOG"

# Docker-guard preflight: wait out any wedge/overload before launching Docker-heavy work.
for i in $(seq 1 120); do
  sh=$(pgrep -c containerd); ld=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
  if [ "$sh" -le 45 ] && [ "$ld" -le 100 ]; then break; fi
  echo "  preflight wait: shims=$sh load=$ld" >> "$LOG"; sleep 60
done

echo "=== MIMO pass launch $(date -u +%FT%TZ): rolling P=$PAR, 3 runs, early-abort on MiMo-solve ===" >> "$LOG"
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
echo "=== MIMO pass drained $(date -u +%FT%TZ) ===" >> "$LOG"
touch build/pipeline/phaseB_mimo.done
