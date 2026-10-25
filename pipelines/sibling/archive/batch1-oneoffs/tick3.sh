#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/harden_solved.log
# 1) re-gate langchain-ds once (unsound after harden r1)
( bash pipeline/gate_one_ds.sh langchain-ds >> build/langchain-ds/harden.nohup 2>&1
  if [ -f build/langchain-ds/.sound ]; then rm -f build/langchain-ds/.auto_trialed; echo "[re-gate langchain-ds $(date -u +%T)] SOUND -> re-trial" >> $LOG
  else echo "[re-gate langchain-ds $(date -u +%T)] STILL UNSOUND -> ERROR" >> $LOG; fi ) &
# 2) harden the 8 newer solves (round-capped at 3), same logic as harden_solved
MORE="ckan-mcp-server-ds rsdoctor-ds traefik-ds arc-ds ec2-fleet-plugin-ds jetty.project-ds surrealdb-ds n8n-ds"
echo "=== harden MORE(8) START $(date -u +%FT%TZ) C=3 ===" >> "$LOG"
printf '%s\n' $MORE | xargs -P3 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"
  [ -f build/$s/.terminal ] && exit 0
  r=$(cat build/$s/.harden_rounds 2>/dev/null || echo 0); r=$((r+1))
  if [ "$r" -gt 3 ]; then touch build/$s/.terminal; echo "[$s] harden cap(3) -> terminal (dropped, solvable)" >> build/pipeline/harden_solved.log; exit 0; fi
  echo "$r" > build/$s/.harden_rounds
  sleep $((RANDOM%20))
  ./drive.sh deepseek bash run_harden.sh "$s" >> build/$s/harden.nohup 2>&1
  bash pipeline/gate_one_ds.sh "$s" >> build/$s/harden.nohup 2>&1
  if [ -f build/$s/.sound ]; then rm -f build/$s/.auto_trialed; echo "[harden+gate $s r$r $(date -u +%T)] SOUND -> cleared .auto_trialed" >> build/pipeline/harden_solved.log
  else echo "[harden+gate $s r$r] UNSOUND after harden" >> build/pipeline/harden_solved.log; fi
' _ {} &
# 3) re-trial the fresh (cleared by hardening): auto_trial_launch skips .auto_trialed, launches cleared ones
sleep 2
bash pipeline/auto_trial_launch.sh >> build/pipeline/auto_trial.log 2>&1 &
wait
echo "TICK3-DONE $(date -u +%FT%TZ)" >> "$LOG"
