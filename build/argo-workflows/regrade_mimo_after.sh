#!/bin/bash
cd /Users/dev/terminal-bench/cwe-bench
while pgrep -f "gate_then_regrade.sh" >/dev/null; do sleep 30; done
if tail -1 build/argo-workflows/gate-20261016b.log | grep -q PASSED; then
  python3 build/regrade_from_code.py /Users/dev/.tb-graders/cwe/jobs/argo-workflows-mimo-r11-20261015-193925-n001/argo-workflows__b5WYen5/ "2026-10-16: sync test now answers the access review per resource (configmaps), like real RBAC; this run gated on workflows" > build/argo-workflows/regrade-mimo-r11-20261016.log 2>&1
fi
