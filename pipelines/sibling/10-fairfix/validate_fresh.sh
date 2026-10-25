#!/bin/bash
# New-order validation for an already-built+gated task (single model, no Opus):
#   fairness FIRST -> if NOT READY: fairfix -> fairness -> ... (<=MAX) -> once READY: gate, trial BOTH.
# Use for: MiMo-lane tasks and the DS-solved leakage re-check (a task that was "solved" only via a
# leak will, after fairfix strips the leak, flip to a DeepSeek fail).
# Never trials a task that did not reach READY (until 2026-10-20 it trialed anyway and marked it
# .sound with no gate); a fairness ERROR or an unfinished fairfix stops it for a person.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
. pipelines/sibling/10-fairfix/validate_common.sh
S=$1; MAX=${2:-3}
LOG=build/pipeline/vfresh_$S.log
echo "=== validate_fresh $S $(date -u +%FT%TZ) ===" >> "$LOG"
ready=no
for r in $(seq 1 "$MAX"); do
  "$CWE_DRIVE" deepseek bash pipelines/sibling/9-fairness/run_fairness.sh "$S" >> "build/$S/vfresh.nohup" 2>&1
  v=$(python3 "$CWE_FAIRNESS_VERDICT" "$S")
  echo "[r$r] fairness=$v $(date -u +%T)" >> "$LOG"
  case "$v" in
    READY*) ready=yes; break ;;
    NOT_READY*) ;;
    *) echo "STOPPED (fairness $v)" > "build/$S/VFRESH_RESULT.txt"; exit 1 ;;
  esac
  if ! "$CWE_DRIVE" deepseek bash pipelines/sibling/10-fairfix/run_fairfix.sh "$S" >> "build/$S/vfresh.nohup" 2>&1; then
    echo "[r$r] fairfix did not finish ($(cat build/$S/fairfix_status.txt 2>/dev/null)); task restored -> stop" >> "$LOG"
    echo "STOPPED (fairfix did not finish)" > "build/$S/VFRESH_RESULT.txt"; exit 1
  fi
done
if [ "$ready" = no ]; then
  echo "CANNOT-VALIDATE (NOT READY after $MAX rounds)" | tee -a "$LOG" > "build/$S/VFRESH_RESULT.txt"; exit 0
fi
echo "[fairness READY] gate, then trial both $(date -u +%T)" >> "$LOG"
# A re-trial of the same version: keep the earlier runs aside so this verdict reads only the new ones.
ts=$(date -u +%Y%m%dT%H%M%SZ)
for f in runs_deepseek.log runs_mimo.log trial_detail_deepseek.json trial_detail_mimo.json; do
  [ -f "build/$S/$f" ] && mv "build/$S/$f" "build/$S/$f.vf-$ts"
done
gate_then_trial "$S" "$LOG" || { echo "STOPPED (not sound; see gate_verdict.json)" > "build/$S/VFRESH_RESULT.txt"; exit 1; }
R=$(both_verdict "$S")
echo "[final] $R" >> "$LOG"
echo "$R" > "build/$S/VFRESH_RESULT.txt"
