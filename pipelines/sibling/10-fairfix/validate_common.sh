# validate_common.sh — sourced by validate_loop.sh / validate_fresh.sh / backstage_validate.sh.
# The steps those scripts share, each of which until 2026-10-20 could turn an error into a verdict:
#   gate_then_trial  re-GATE before trialing (they used to `touch .sound` with no gate at all)
#   both_verdict     per-model state from pipeline/trial_state.py (they used to grep "1.0" as a
#                    regex, so "0.9231,0.5" read as a solve, and an all-infra-error run as a fail)
# The verdict these print is PROVISIONAL: per-model verdicts come from build/audit_results.py
# after the post-run audit.

# gate_then_trial SLUG LOG : gate the task; trial both models only if it is sound. Returns 1 if not.
gate_then_trial() {
  local S=$1 LOG=$2 g
  g=$(bash pipeline/gate_one_ds.sh "$S" 2>&1 | tail -1)
  echo "[gate $(date -u +%T)] $g" >> "$LOG"
  [ -f "build/$S/.sound" ] || { echo "[gate] not sound -> NOT trialed" >> "$LOG"; return 1; }
  python3 build/trial.py "$S" --models deepseek --no-verdict >> "build/$S/trial_deepseek.out" 2>&1 &
  local p1=$!
  python3 build/trial.py "$S" --models mimo --no-verdict >> "build/$S/trial_mimo.out" 2>&1 &
  local p2=$!
  wait $p1 $p2
  return 0
}

# both_verdict SLUG : one line, "<verdict> | ds: <state> | mm: <state>"
both_verdict() {
  local S=$1 D M d m R
  D=$(python3 pipeline/trial_state.py "$S" deepseek); M=$(python3 pipeline/trial_state.py "$S" mimo)
  d=${D%% *}; m=${M%% *}
  if   [ "$d" = failed ] && [ "$m" = failed ]; then R="** BOTH-MODELS FAIL 3/3 (provisional: confirm with audit_results.py) **"
  elif [ "$d" = solved ] && [ "$m" = solved ]; then R="both solve"
  elif [ "$d" = solved ] && [ "$m" = failed ]; then R="one-sided (MiMo-only fail)"
  elif [ "$d" = failed ] && [ "$m" = solved ]; then R="one-sided (DeepSeek-only fail)"
  elif [ "$d" = solved ] || [ "$m" = solved ]; then R="solved by one model; the other INCOMPLETE ($d/$m)"
  else R="INCOMPLETE (not enough graded runs: ds=$d mm=$m; infrastructure, re-trial)"; fi
  echo "$R | ds: $D | mm: $M"
}
