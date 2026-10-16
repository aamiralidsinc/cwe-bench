#!/bin/bash
# 2026-10-16: re-gate argo after the RBAC-faithful sync test, then regrade DeepSeek r11 (gated on
# "workflows") and, as a control, keep the result honest either way.
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py argo-workflows > build/argo-workflows/gate-20261016b.log 2>&1
if tail -1 build/argo-workflows/gate-20261016b.log | grep -q PASSED; then
  python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/argo-workflows-deepseek-r11-20261015-193852-n001/argo-workflows__QprUNQg \
    "2026-10-16: sync test now answers the access review per resource (configmaps), like real RBAC; this run gated on workflows" \
    > build/argo-workflows/regrade-QprUNQg-20261016.log 2>&1
fi
