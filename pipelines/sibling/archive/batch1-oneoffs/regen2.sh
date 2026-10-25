#!/bin/bash
# flyto-core-ds: archive the current blind patch, regenerate on DeepSeek, gate. airflow-ds: re-gate.
cd "$HOME/cwe-bench" || exit 1
ts=$(date -u +%Y%m%dT%H%M%SZ); L=build/pipeline/regen2-$ts.log
a=$HOME/.tb-graders/cwe/blind-archive/flyto-core-ds-$ts; mkdir -p "$a"
cp -a build/flyto-core-ds/checks/blind.patch build/flyto-core-ds/blind-run.json build/flyto-core-ds/gate_verdict.json "$a/" 2>/dev/null
cp -a "$HOME/.tb-graders/cwe/blind/flyto-core-ds/mechanisms.md" "$a/" 2>/dev/null
echo "=== regen2 start $(date -u +%FT%TZ); flyto old blind archived to $a" >> "$L"
(
  ./drive.sh deepseek bash run_blindfix.sh flyto-core-ds >> build/flyto-core-ds/blindfix.nohup 2>&1; rc=$?
  echo "[flyto blind] exit=$rc status=$(cat build/flyto-core-ds/blind_status.txt) $(date -u +%T)" >> "$L"
  if [ $rc -eq 0 ]; then echo "[flyto gate] $(bash pipeline/gate_one_ds.sh flyto-core-ds 2>&1 | tail -1) $(date -u +%T)" >> "$L"
  else echo "[flyto gate] skipped: no new blind patch" >> "$L"; fi
  echo "[flyto done]" >> "$L"
) &
(
  sleep 20
  echo "[airflow gate] $(bash pipeline/gate_one_ds.sh airflow-ds 2>&1 | tail -1) $(date -u +%T)" >> "$L"
  echo "[airflow done]" >> "$L"
) &
wait
echo "=== regen2 done $(date -u +%FT%TZ)" >> "$L"
