#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
L=build/theia-ds/fairfix-pipeline.log; : > "$L"
echo "=== theia-ds fairfix pipeline START $(date -u +%FT%TZ) ===" >> "$L"
# 1) snapshot current (v2) before the in-place fairfix edit
bash pipeline/snapshot_experiment.sh theia-ds >> "$L" 2>&1
echo "[1] snapshot done; VERSION=$(cat build/theia-ds/VERSION)" >> "$L"
# 2) DeepSeek fairfix (applies the required instruction/fixture change the NOT_READY verdict named)
./drive.sh deepseek bash run_fairfix.sh theia-ds >> "$L" 2>&1
echo "[2] fairfix done $(date -u +%T)" >> "$L"
# 3) full gate (fairfix changes tests/instruction -> container gate)
bash pipeline/gate_one_ds.sh theia-ds >> "$L" 2>&1
echo "[3] gate done: sound=$([ -f build/theia-ds/.sound ]&&echo Y||echo N) unsound=$([ -f build/theia-ds/.unsound ]&&echo Y||echo N)" >> "$L"
# 4) if sound, re-trial both models (3h, early-abort); else stop for human
if [ -f build/theia-ds/.sound ] && [ ! -f build/theia-ds/.unsound ]; then
  rm -f build/theia-ds/.terminal build/theia-ds/.auto_trialed; touch build/theia-ds/.auto_trialed
  setsid bash -c "cd \$HOME/cwe-bench; CWE_AGENT_TIMEOUT_MULT=1 python3 build/trial.py theia-ds >> build/theia-ds/auto_trial.out 2>&1; echo \"[trial-done theia-ds v3 \$(date -u +%T)]\" >> build/pipeline/auto_trial.log" >/dev/null 2>&1 </dev/null &
  echo "[4] SOUND -> re-trial launched (both models)" >> "$L"
else
  echo "[4] NOT SOUND after fairfix -> STOP, human review needed" >> "$L"
fi
echo "THEIA-FAIRFIX-PIPELINE-DONE" >> "$L"
