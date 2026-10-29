#!/bin/bash
# Repair mode of the fairfix step: the agent half of the work queue's `repair` job (owner 2026-10-28).
# History: the repair step already existed as this fairfix step (run_fairfix.sh, and run_fairfix_stack.sh for stacked
# tasks); an Opus orchestrator started it and the work ran on the VM through DeepSeek. It was lost when the pipeline
# moved to the SQLite work queue (no repair job kind), and repairs were then done by hand with Opus sub-agents. The
# queue's repair job (common/queue/repairjob.py, kinds/repair.py) brings it back on DeepSeek, and passes the failing
# runs' evidence that fairfix never received (the hardening step got trial_summary.md on 2026-10-21; fairfix did not).
#
# Started by run_fairfix.sh / run_fairfix_stack.sh when REPAIR_INPUTS is set; the job sets it, never a person:
#   common/launch/drive.sh deepseek python3 -I common/queue/repairjob.py SLUG     (the job runs the fairfix script)
# Env: MODEL (drive.sh), REPAIR_INPUTS (build/SLUG/repair-inputs-<UTC>/), REPAIR_DATE (YYYYMMDD), REPAIR_ID (the
# repair's own id, the <UTC> of its inputs folder: it names repaired-tests-<id>-repair/, removed-tests-<id>-repair/ and
# history/<id>-repair.md, so a second repair on the same day gets new folders; 2026-10-29, cline-s2 #2741),
# FAIRFIX_TIMEOUT (default 10800). The job holds the task, backs it up, checks the agent's work and restores the
# originals when a check fails: this script only runs the agent. No snapshot_experiment.sh here: a post-run repair
# keeps the runs in jobs/ so the queue can regrade them on the repaired tests (the snapshot would move them away).
# Writes build/SLUG/repair-run.json, repair-run.err, repair-exit.txt, repair_start.txt, repair_end.txt,
# repair_status.txt (agent_status.py: `ok` or `error: ...`). Exit 0 = the agent finished; 1 = it did not.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: run_repair_agent.sh SLUG [--stacked]}; STACKED=0; [ "${2:-}" = --stacked ] && STACKED=1
cd "$CWE_ROOT" || exit 1
B=build/$SLUG
[ -n "${MODEL:-}" ] || { echo "error: MODEL not set; the repair job launches this through common/launch/drive.sh deepseek" | tee "$B/repair_status.txt"; exit 1; }
[ -d "${REPAIR_INPUTS:-}" ] || { echo "error: REPAIR_INPUTS is not a folder (${REPAIR_INPUTS:-unset})" | tee "$B/repair_status.txt"; exit 1; }
D=${REPAIR_DATE:-$(date -u +%Y%m%d)}
ID=${REPAIR_ID:-$(basename "$REPAIR_INPUTS" | sed -n 's/^repair-inputs-//p')}
[ -n "$ID" ] || ID=$(date -u +%Y%m%dT%H%M%SZ)
SCRATCH="$HOME/.tb-graders/cwe/work/$SLUG/repair-$ID"
mkdir -p "$SCRATCH"
fill() { sed -e "s|{{SLUG}}|$SLUG|g" -e "s|{{ROOT}}|$CWE_ROOT|g" -e "s|{{INPUTS}}|$REPAIR_INPUTS|g" \
             -e "s|{{DATE}}|$D|g" -e "s|{{REPAIR_ID}}|$ID|g" -e "s|{{SCRATCH}}|$SCRATCH|g"; }
P=$(sed -n '/^---8<---$/,$p' "$CWE_COMMON/fairness/REPAIR-BRIEF.md" | tail -n +2 | fill)
# The other-reading check of the repair step (client audit PO-3, common/fairness/OTHER-READING-CHECK.md).
if [ -f "$CWE_COMMON/fairness/OTHER-READING-CHECK.md" ]; then
  P="$P

$(sed -n '/^---8<---$/,$p' "$CWE_COMMON/fairness/OTHER-READING-CHECK.md" | tail -n +2)

Report also, for each other_reading check, the PASS / FAIL / MISSING result per test and the repair you made."
fi
if [ "$STACKED" = 1 ]; then
  P="$P

This is a STACKED task. Also apply these rules (instruction changes are not allowed in a repair):
$(sed -n "/^---8<---$/,\$p" pipelines/stacking/7-fairness/STACKING-FAIRNESS-ADDENDUM.md | tail -n +2)"
fi
echo "running" > "$B/repair_status.txt"
date -u +%FT%TZ > "$B/repair_start.txt"
timeout "${FAIRFIX_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --permission-mode bypassPermissions --add-dir "$CWE_ROOT" --add-dir "$CWE_DATA_ROOT" \
  --add-dir "$HOME/.tb-graders/cwe/work" --add-dir "$HOME/.tb-graders/cwe/jobs" \
  --output-format json > "$B/repair-run.json" 2> "$B/repair-run.err" < /dev/null
rc=$?
echo $rc > "$B/repair-exit.txt"
date -u +%FT%TZ > "$B/repair_end.txt"
st=$(python3 "$CWE_AGENT_STATUS" "$B/repair-run.json" "$rc" --details "$B/repair_status.json")
echo "$st" > "$B/repair_status.txt"
echo "$SLUG repair agent: exit $rc; $st"
[ "$st" = ok ]
