#!/bin/bash
# 2026-10-16: re-gate rclone and rclone-sib after stating the auth-proxy contract (_secret_access_key)
# and adding the no-secret test. On PASS: earlier runs no longer count (task_defects, fixed_utc = now)
# and the tasks rejoin the offline queue from now on (fresh runs, numbered r21+).
cd /Users/dev/terminal-bench/cwe-bench
ok=1
for t in rclone rclone-sib; do
  caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py $t > build/$t/gate-20261016-contract.log 2>&1
  tail -1 build/$t/gate-20261016-contract.log | grep -q PASSED || { ok=0; echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: $t gate FAILED after contract repair; not released" >> build/audit/offline_queue.log; }
done
if [ $ok = 1 ]; then
  NOW=$(date -u +%Y-%m-%dT%H:%M)
  for t in rclone rclone-sib; do
    printf '%s\t%s\tunstated-contract\tcorrect-secret tests relied on the _secret_access_key proxy field, which only the upstream fix documents; the instruction now states it (2026-10-16). Earlier runs do not count.\n' $t $NOW >> build/audit/task_defects.tsv
    printf '%s\t%s\n' $t $NOW >> build/audit/offline_since.tsv
  done
  echo "${NOW}Z switch: rclone + rclone-sib re-gated with the stated proxy contract; released (fresh runs r21+)" >> build/audit/offline_queue.log
fi
