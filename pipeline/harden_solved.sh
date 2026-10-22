#!/bin/bash
# Harden the solved (non-breaker, sound) tasks. Two verdicts per task, both from the hardening agent:
#   PRE  (can_harden): false -> the task is REMOVED (dropped; it stays a valid solvable task, just not
#        shipped as a breaker candidate).  true -> it is hardened + converted to the Frontier format.
#   POST (fail_confidence low|med|high): recorded after a clean re-gate; the predicted likelihood both
#        models still fail, before any trial.
# A round counts only when the agent hardened AND changed the task (run_harden.sh exit 0). The
# 2026-10-20 wiring bug (run_harden.sh called without the pipeline/ prefix -> agent never ran) is fixed;
# this calls pipeline/run_harden.sh via drive.sh.
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/harden_solved.log
# Default: the 11-task test set. Override by passing slugs as args (used when scaling to all 36).
SOLVED="${*:-langchain-ds prompty-ds mcp-atlassian-ds new-api-ds whistle-ds gogs-ds limesurvey-ds vitest-ds grav-ds compliance-trestle-ds ghost-ds}"
PAR="${HARDEN_PAR:-4}"
{
echo "=== harden solved START $(date -u +%FT%TZ) C=$PAR (round cap 3) tasks: $SOLVED ==="
printf '%s\n' $SOLVED | xargs -P"$PAR" -I{} bash -c '
  s="$1"; cd "$HOME/cwe-bench"; L=build/pipeline/harden_solved.log
  [ -f build/$s/.terminal ] && { echo "[$s] already terminal, skip" >> $L; exit 0; }
  pgrep -af "[r]un_harden.sh $s" >/dev/null && { echo "[$s] harden already live, skip" >> $L; exit 0; }
  r=$(cat build/$s/.harden_rounds 2>/dev/null || echo 0); r=$((r+1))
  if [ "$r" -gt 3 ]; then touch build/$s/.terminal; echo "[$s] harden cap(3) reached -> terminal (dropped, stays solvable)" >> $L; exit 0; fi
  sleep $((RANDOM%30))
  ./drive.sh deepseek bash pipeline/run_harden.sh "$s" >> build/$s/harden.nohup 2>&1; hrc=$?
  case $hrc in
    4)  # PRE-verdict can_harden=false -> remove/drop the task
      reason=$(python3 -c "import json;print(json.load(open(\"build/$s/harden_verdict.json\")).get(\"reason\",\"\"))" 2>/dev/null)
      touch build/$s/.terminal build/$s/.harden_removed
      echo "[REMOVED $s r$r $(date -u +%T)] can_harden=false -> dropped: $reason" >> $L
      exit 0 ;;
    0) : ;;  # hardened + changed -> re-gate below
    *)  echo "[harden $s r$r $(date -u +%T)] NOT a round (exit $hrc): $(cat build/$s/harden_status.txt 2>/dev/null)" >> $L
      exit 0 ;;
  esac
  echo "$r" > build/$s/.harden_rounds
  bash pipeline/gate_one_ds.sh "$s" >> build/$s/harden.nohup 2>&1; grc=$?
  fc=$(python3 -c "import json;print(json.load(open(\"build/$s/harden_verdict.json\")).get(\"fail_confidence\"))" 2>/dev/null)
  nlev=$(python3 -c "import json;print(len(json.load(open(\"build/$s/harden_verdict.json\")).get(\"levers\",[])))" 2>/dev/null)
  case $grc in
    0) rm -f build/$s/.auto_trialed
       echo "[HARDENED $s r$r $(date -u +%T)] SOUND+conformant; levers=$nlev fail_confidence=$fc -> cleared .auto_trialed for re-trial" >> $L ;;
    1) echo "[harden+gate $s r$r] UNSOUND after harden (agent re-gate should have passed; quality issue: $(python3 -c "import json;d=json.load(open(\"build/$s/gate_verdict.json\"));print(d.get(\"stage\"))" 2>/dev/null))" >> $L ;;
    *) echo "[harden+gate $s r$r] GATE-ERROR after harden (infra/gate, re-gate it)" >> $L ;;
  esac
' _ {}
echo "=== harden solved DONE $(date -u +%FT%TZ) ==="; echo HARDEN-SOLVED-DONE
} >> "$LOG" 2>&1
