#!/bin/bash
# 2026-10-16: re-gate filament after the upload-test repair (any refusal); regrade MiMo r11; release.
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py filament > build/filament/gate-20261016.log 2>&1
if tail -1 build/filament/gate-20261016.log | grep -q PASSED; then
  python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/filament-mimo-r11-20261015-201112-n001/filament__nQD6JG9 \
    "2026-10-16: upload tests accept any refusal (exception or 4xx), not only 403" > build/filament/regrade-nQD6JG9.log 2>&1
  printf 'filament\t2026-10-15T23:35\n' >> build/audit/offline_since.tsv
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: filament upload tests repaired, gate PASSED, MiMo r11 regraded, released" >> build/audit/offline_queue.log
else
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: filament gate FAILED after repair; not released" >> build/audit/offline_queue.log
fi
