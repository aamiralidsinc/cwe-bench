#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
L=build/pipeline/batch_2026-10-21.log; : > "$L"
echo "=== batch launch $(date -u +%FT%TZ) ===" >> "$L"
# 1) DeepSeek fairness on the 4 both-fail candidates lacking a current GATE_A
for s in mockoon-ds flowise-ds hubuum-client-rust-ds hermes-agent-ds; do
  setsid bash -c "cd \$HOME/cwe-bench; ./drive.sh deepseek bash run_fairness.sh $s >> build/$s/fairness.nohup 2>&1" >/dev/null 2>&1 </dev/null & disown
  echo "[fairness launched] $s" >> "$L"
done
# 2) trials on the 12 recovered tasks (both models, early-abort, 3h, staggered)
for s in astro-ds keras-ds flyto-core-ds portainer-ds fission-ds coreutils-ds knowns-ds openbao-ds orval-ds tinacms-ds vibe-trading-ds yamcs-ds; do
  [ -f build/$s/.sound ] || { echo "[skip $s] not sound" >> "$L"; continue; }
  rm -f build/$s/.terminal build/$s/.auto_trialed; touch build/$s/.auto_trialed
  setsid bash -c "sleep \$((RANDOM%40)); cd \$HOME/cwe-bench; CWE_AGENT_TIMEOUT_MULT=1 python3 build/trial.py $s >> build/$s/auto_trial.out 2>&1; echo \"[trial-done $s \$(date -u +%T)] \$(grep -h 'ACCEPTED\|solved run' build/$s/auto_trial.out|tail -1)\" >> build/pipeline/batch_2026-10-21.log" >/dev/null 2>&1 </dev/null & disown
  echo "[trial launched] $s" >> "$L"
done
echo "BATCH-LAUNCH-DONE $(date -u +%FT%TZ)" >> "$L"
