#!/bin/bash
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py webob > build/webob/gate-20261016b.log 2>&1
if tail -1 build/webob/gate-20261016b.log | grep -q PASSED; then
  python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/webob-mimo-r11-20261015-214806-n001/webob__CeNzGqe \
    "2026-10-16: removed test_exception_bare_protocol_relative, which contradicted the instruction's scope" > build/webob/regrade-CeNzGqe.log 2>&1
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: webob bare-protocol-relative test removed, gate PASSED, MiMo r11 regraded" >> build/audit/offline_queue.log
else
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: webob gate FAILED after test removal" >> build/audit/offline_queue.log
fi
