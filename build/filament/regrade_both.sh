#!/bin/bash
# 2026-10-16: redo the filament regrades with the fixed replay (newline markers, cache paths skipped).
cd /Users/dev/terminal-bench/cwe-bench
WHY="2026-10-16: upload tests accept any refusal; replay fixed (missing-newline markers, cache paths skipped)"
python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/filament-mimo-r11-20261015-201112-n001/filament__nQD6JG9 "$WHY" > build/filament/regrade-nQD6JG9-b.log 2>&1
python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/filament-deepseek-r12-20261015-205636-n001/filament__ShThBfS "$WHY" > build/filament/regrade-ShThBfS-b.log 2>&1
