#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
L=build/pipeline/six_unresolved.log; : > "$L"
echo "=== 6 unresolved clean re-trials START $(date -u +%FT%TZ) ===" >> "$L"
SIX="airflow-ds hermes-agent-ds mockoon-ds flowise-ds hubuum-client-rust-ds siyuan-ds"
printf '%s\n' $SIX | xargs -P6 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"; sleep $((RANDOM%20))
  echo "[start $s $(date -u +%T)] snapshot+clean+trial" >> build/pipeline/six_unresolved.log
  # archive old mixed/partial runs for a clean 3/3 (no task edit; just a clean slate)
  bash pipeline/snapshot_experiment.sh "$s" >> build/pipeline/six_unresolved.log 2>&1
  rm -f build/$s/.terminal build/$s/.auto_trialed
  # fresh both-model trial, early-abort, 3h/run (not inflated), full 3 runs each on a non-solve
  CWE_AGENT_TIMEOUT_MULT=1 python3 build/trial.py "$s" --full >> build/$s/auto_trial.out 2>&1
  acc=$(grep -h "ACCEPTED\|solved run" build/$s/auto_trial.out 2>/dev/null | tail -1)
  echo "[done $s $(date -u +%T)] $acc" >> build/pipeline/six_unresolved.log
' _ {} &
wait
echo "SIX-UNRESOLVED-DONE $(date -u +%FT%TZ)" >> "$L"
