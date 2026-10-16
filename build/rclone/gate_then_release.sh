#!/bin/bash
# 2026-10-16: re-gate rclone after the correct-secret proxy tests; release it to the offline queue on PASS.
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py rclone > build/rclone/gate-20261016.log 2>&1
if tail -1 build/rclone/gate-20261016.log | grep -q PASSED; then
  printf 'rclone\t%s\n' "$(date -u +%Y-%m-%dT%H:%M)" >> build/audit/offline_since.tsv
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: rclone re-gated (correct-secret proxy tests) and released" >> build/audit/offline_queue.log
else
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: rclone gate FAILED; not released" >> build/audit/offline_queue.log
fi
