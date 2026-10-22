#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/harden_solved.log
# 1) record protobuf.js as BREAKER (GATE_A READY on a both-fail)
touch build/protobuf.js-ds/.terminal
echo "[BREAKER protobuf.js-ds $(date -u +%FT%TZ)] both-fail 3/3 + fairness GATE_A READY -> CONFIRMED both-model breaker (NEEDS_HUMAN_REVIEW:YES, flag for user)" >> "$LOG"
# 2) DeepSeek fairness on the 4 both-fail candidates (parallel; load idle)
for s in theia-ds seaweedfs-ds summarize-ds trivy-ds; do
  [ -f build/$s/.sound ] || { echo "[fairness skip $s] not sound" >> "$LOG"; continue; }
  setsid bash -c "./drive.sh deepseek bash run_fairness.sh $s >> build/$s/fairness.nohup 2>&1" >/dev/null 2>&1 </dev/null &
  disown
done
# 3) re-trial typo3 (fairfix made it sound; confirm still both-fail under fixed tests)
rm -f build/typo3-ds/.auto_trialed
setsid bash -c "CWE_AGENT_TIMEOUT_MULT=1.5 python3 build/trial.py typo3-ds >> build/typo3-ds/auto_trial.out 2>&1; echo \"[typo3 re-trial-done \$(date -u +%T)] ds=[\$(grep -oE 'reward=[0-9.]+' build/typo3-ds/runs_deepseek.log 2>/dev/null|tail -3|paste -sd, -)] mm=[\$(grep -oE 'reward=[0-9.]+' build/typo3-ds/runs_mimo.log 2>/dev/null|tail -3|paste -sd, -)]\" >> build/pipeline/auto_trial.log" >/dev/null 2>&1 </dev/null &
disown
touch build/typo3-ds/.auto_trialed
sleep 4
echo "launched: protobuf.js=BREAKER; fairness on theia/seaweedfs/summarize/trivy; typo3 re-trial"
echo "fair procs=$(pgrep -af '[r]un_fairness.sh'|wc -l) typo3 trial=$(pgrep -af '[t]rial.py typo3'|wc -l)"
