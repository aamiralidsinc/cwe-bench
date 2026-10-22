#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/harden_solved.log
echo "=== CONVERGE tick12 START $(date -u +%FT%TZ) ===" >> "$LOG"
# 1) DROP tasks that reached cap (harden_rounds==3) and are sound -> terminal (still-solvable, per cap-3 policy)
for d in build/*/; do s=$(basename "$d")
  [ -f build/$s/.terminal ] && continue
  r=$(cat build/$s/.harden_rounds 2>/dev/null || echo 0)
  if [ "$r" -ge 3 ] && [ -f build/$s/.sound ]; then
    touch build/$s/.terminal
    echo "[DROP $s] cap-3 reached, solved across all rounds -> TERMINAL (fair+solvable, not a breaker)" >> "$LOG"
  fi
done
# 2) HARDEN tasks at round 2 -> round 3 (skip if harden already live)
R2=$(for d in build/*/; do s=$(basename "$d"); [ -f build/$s/.terminal ] && continue; [ "$(cat build/$s/.harden_rounds 2>/dev/null||echo 0)" = "2" ] && [ -f build/$s/.sound ] && echo "$s"; done)
echo "=== harden r2->r3 batch: $R2 ===" >> "$LOG"
printf '%s\n' $R2 | xargs -P3 -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"; [ -z "$s" ] && exit 0
  [ -f build/$s/.terminal ] && exit 0
  pgrep -af "[r]un_harden.sh $s" >/dev/null && exit 0
  r=$(cat build/$s/.harden_rounds 2>/dev/null||echo 0); r=$((r+1)); echo "$r" > build/$s/.harden_rounds
  sleep $((RANDOM%20))
  ./drive.sh deepseek bash run_harden.sh "$s" >> build/$s/harden.nohup 2>&1
  bash pipeline/gate_one_ds.sh "$s" >> build/$s/harden.nohup 2>&1
  if [ -f build/$s/.sound ]; then rm -f build/$s/.auto_trialed; echo "[harden+gate $s r$r $(date -u +%T)] SOUND -> cleared" >> build/pipeline/harden_solved.log
  else echo "[harden+gate $s r$r] UNSOUND after harden" >> build/pipeline/harden_solved.log; fi
' _ {} &
# 3) re-trial fresh pool (r1 tasks + any cleared not-yet-dropped)
sleep 3
bash pipeline/auto_trial_launch.sh >> build/pipeline/auto_trial.log 2>&1 &
wait
echo "TICK12-DONE $(date -u +%FT%TZ) terminals=$(ls build/*/.terminal 2>/dev/null|wc -l)" >> "$LOG"
