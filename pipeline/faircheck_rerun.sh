#!/bin/bash
# Re-run the FIXED (two-gate) DeepSeek faircheck on all 11 candidates, originals restored.
# No Docker (Read/Grep/Glob/Write) so it is safe alongside the gates. Detached.
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/faircheck_rerun.log
TASKS="litellm-ds protobuf.js-ds airflow-ds hazelcast-ds hermes-agent-ds siyuan-ds electron-builder-credential-leakage flowise-cross-tenant-inj prompty-path-read-inj vitest-api-fs-authz-inj airflow-info-exposure-inj"
{
echo "=== faircheck_rerun START $(date -u +%FT%TZ) (two-gate brief) ==="
for s in $TASKS; do mv "build/$s/FAIRNESS.md" "build/$s/FAIRNESS.md.preFix" 2>/dev/null; done
printf '%s\n' $TASKS | xargs -P4 -I{} bash -c 'cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_fairness.sh "$1" >> "build/$1/faircheck.nohup" 2>&1' _ {}
echo "=== faircheck_rerun DONE $(date -u +%FT%TZ) ==="
for s in $TASKS; do echo "  $s: $(python3 pipeline/fairness_verdict.py "$s")"; done   # last GATE_A line; ERROR if none
echo ALL-FAIRCHECK-DONE
} >> "$LOG" 2>&1
