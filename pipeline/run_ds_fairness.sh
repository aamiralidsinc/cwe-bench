#!/bin/bash
# DeepSeek does its own fairness review of DeepSeek-built tasks (single-model pipeline).
# The developer (not Opus) audits the result afterward to verify the component works.
cd "$HOME/cwe-bench" || exit 1
for s in "$@"; do
  rm -f "build/$s/FAIRNESS.md"
  nohup ./drive.sh deepseek bash run_fairness.sh "$s" > "build/$s/fairness_ds.nohup" 2>&1 < /dev/null &
  echo "DeepSeek self-fairness $s pid $!"
done
sleep 12
echo "fairness agents now: $(ps -eo cmd | grep -c '[r]un_fairness.sh') | load=$(cut -d' ' -f1 /proc/loadavg)"
