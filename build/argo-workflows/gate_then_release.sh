#!/bin/bash
# 2026-10-16: re-gate argo after hardening the template access-review stubs; release it to the queue on PASS.
cd /Users/dev/terminal-bench/cwe-bench
caffeinate -i ~/.local/share/uv/tools/harbor/bin/python builder/gate.py argo-workflows > build/argo-workflows/gate-20261016c.log 2>&1
if tail -1 build/argo-workflows/gate-20261016c.log | grep -q PASSED; then
  printf 'argo-workflows\t2026-10-15T23:35\n' >> build/audit/offline_since.tsv   # original switch time
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: argo-workflows template tests hardened, gate PASSED, released" >> build/audit/offline_queue.log
else
  echo "$(date -u +%Y-%m-%dT%H:%M)Z switch: argo-workflows gate FAILED after template hardening; NOT released — revert needed" >> build/audit/offline_queue.log
fi
