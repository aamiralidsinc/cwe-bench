#!/bin/bash
# Iteratively validate a breaker candidate on a single model (DeepSeek), no Opus:
#   round: fairfix (apply current FAIRNESS.md) -> fairness re-check
#   when fairness READY: re-GATE, then re-trial BOTH target models -> provisional verdict
#   if still NOT READY after MAX rounds: cannot cleanly validate (likely not a fair task)
#   a fairness ERROR or an unfinished fairfix stops the loop for a person
# Detached (setsid). Writes build/pipeline/validate_<slug>.log
cd "$HOME/cwe-bench" || exit 1
. pipeline/validate_common.sh
S=$1; MAX=${2:-3}
LOG=build/pipeline/validate_$S.log
echo "=== validate_loop $S start $(date -u +%FT%TZ) ===" >> "$LOG"
for r in $(seq 1 "$MAX"); do
  echo "[r$r] fairfix $(date -u +%T)" >> "$LOG"
  if ! ./drive.sh deepseek bash run_fairfix.sh "$S" >> "build/$S/validate.nohup" 2>&1; then
    echo "[r$r] fairfix did not finish ($(cat build/$S/fairfix_status.txt 2>/dev/null)); task restored -> stop" >> "$LOG"
    echo "STOPPED (fairfix did not finish; see validate_$S.log)" > "build/$S/VALIDATE_RESULT.txt"; exit 1
  fi
  echo "[r$r] fairness $(date -u +%T)" >> "$LOG"
  ./drive.sh deepseek bash run_fairness.sh "$S" >> "build/$S/validate.nohup" 2>&1
  v=$(python3 pipeline/fairness_verdict.py "$S")
  echo "[r$r] fairness verdict: $v" >> "$LOG"
  case "$v" in
    READY*)
      echo "[r$r] READY -> gate, then re-trial both models $(date -u +%T)" >> "$LOG"
      if ! gate_then_trial "$S" "$LOG"; then
        echo "STOPPED (not sound after fairfix; see gate_verdict.json)" > "build/$S/VALIDATE_RESULT.txt"; exit 1
      fi
      R=$(both_verdict "$S")
      echo "[r$r] FINAL: $R" >> "$LOG"
      echo "$R" > "build/$S/VALIDATE_RESULT.txt"
      exit 0 ;;
    NOT_READY*) ;;
    *) echo "STOPPED (fairness $v)" > "build/$S/VALIDATE_RESULT.txt"; exit 1 ;;
  esac
done
echo "=== $S stayed NOT READY after $MAX rounds -> CANNOT CLEANLY VALIDATE (likely not a fair task) $(date -u +%T) ===" >> "$LOG"
echo "CANNOT-VALIDATE (NOT READY after $MAX fairfix rounds)" > "build/$S/VALIDATE_RESULT.txt"
