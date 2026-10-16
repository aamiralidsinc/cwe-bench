#!/bin/bash
# 2026-10-16: re-gate trigger-dev after the check-completion test repair; regrade DeepSeek r11; release.
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py trigger-dev > build/trigger-dev/gate-20261016c.log 2>&1
if tail -1 build/trigger-dev/gate-20261016c.log | grep -q PASSED; then
  python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/trigger-dev-deepseek-r11-20261015-205938-n001/trigger-dev__aoMpPQa \
    "2026-10-16: check-completion tests repaired (any refusal; either batch id form)" > build/trigger-dev/regrade-aoMpPQa.log 2>&1
  printf 'trigger-dev\t2026-10-15T23:35\n' >> build/audit/offline_since.tsv
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: trigger-dev check-completion tests repaired, gate PASSED, r11 regraded, released" >> build/audit/offline_queue.log
else
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: trigger-dev gate FAILED after repair; not released" >> build/audit/offline_queue.log
fi
