#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/harden_solved.log
# harden newly-solved completions NOT in active batch7 set (round-capped 3)
HB="compliance-trestle-ds jetty.project-ds pimcore-ds hazelcast-ds"
echo "=== harden batch9 START $(date -u +%FT%TZ) [$HB] C=2 ===" >> "$LOG"
printf '%s\n' $HB | xargs -P2 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"
  [ -f build/$s/.terminal ] && exit 0
  # skip if a harden is already live for this task
  pgrep -af "[r]un_harden.sh $s" >/dev/null && { echo "[$s] harden already live, skip" >> build/pipeline/harden_solved.log; exit 0; }
  r=$(cat build/$s/.harden_rounds 2>/dev/null || echo 0); r=$((r+1))
  if [ "$r" -gt 3 ]; then touch build/$s/.terminal; echo "[$s] harden cap(3) -> TERMINAL (dropped, solvable)" >> build/pipeline/harden_solved.log; exit 0; fi
  echo "$r" > build/$s/.harden_rounds
  sleep $((RANDOM%20))
  ./drive.sh deepseek bash run_harden.sh "$s" >> build/$s/harden.nohup 2>&1
  bash pipeline/gate_one_ds.sh "$s" >> build/$s/harden.nohup 2>&1
  if [ -f build/$s/.sound ]; then rm -f build/$s/.auto_trialed; echo "[harden+gate $s r$r $(date -u +%T)] SOUND -> cleared" >> build/pipeline/harden_solved.log
  else echo "[harden+gate $s r$r] UNSOUND after harden" >> build/pipeline/harden_solved.log; fi
' _ {} &
sleep 3
bash pipeline/auto_trial_launch.sh >> build/pipeline/auto_trial.log 2>&1 &
wait
echo "TICK9-DONE $(date -u +%FT%TZ)" >> "$LOG"
