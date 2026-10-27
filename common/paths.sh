# Repo locations for cwe-bench (shell twin of common/paths.py; keep the two in step).
#
# Source it from any script, at any depth:
#
#   . "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
#
# After that, use the CWE_* variables (absolute paths) and `cd "$CWE_ROOT"` instead of a hard-coded ~/cwe-bench.
# Agent prompts may use repo-relative paths (common/gate/gate.py ...) because every agent runs with cwd = $CWE_ROOT.

# `pwd -P`: the physical path, so a script started through a release's `current` link keeps the release it started
# with even when `current` is repointed while it runs (versioned releases, docs/RELEASES.md).
CWE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
[ -f "$CWE_ROOT/.cwe-bench-root" ] || { echo "common/paths.sh: no .cwe-bench-root at $CWE_ROOT" >&2; return 1 2>/dev/null || exit 1; }
CWE_CODE_ROOT=$CWE_ROOT
# Run data: $CWE_DATA_ROOT, else the release's .cwe-data-root file, else the code root (a plain checkout).
if [ -z "${CWE_DATA_ROOT:-}" ]; then
  if [ -s "$CWE_ROOT/.cwe-data-root" ]; then CWE_DATA_ROOT=$(head -n 1 "$CWE_ROOT/.cwe-data-root"); else CWE_DATA_ROOT=$CWE_ROOT; fi
fi

# run data (stays at the data root; a release links these folders to it)
CWE_BUILD=$CWE_DATA_ROOT/build
CWE_TASKS=$CWE_DATA_ROOT/tasks
CWE_BUILD_PIPELINE=$CWE_BUILD/pipeline
CWE_AUDIT_DIR=$CWE_BUILD/audit
CWE_REPORTS=$CWE_DATA_ROOT/reports

# areas
CWE_COMMON=$CWE_ROOT/common
CWE_SOURCER=$CWE_ROOT/sourcer
CWE_SIBLING=$CWE_ROOT/pipelines/sibling
CWE_STACKING=$CWE_ROOT/pipelines/stacking
CWE_SIBLING_OUT=$CWE_DATA_ROOT/pipelines/sibling/out
CWE_STACKING_OUT=$CWE_DATA_ROOT/pipelines/stacking/out
CWE_ROUTER_OUT=$CWE_DATA_ROOT/pipelines/router/out

# common/launch
CWE_DRIVE=$CWE_COMMON/launch/drive.sh
CWE_RUN_BUILD=$CWE_COMMON/launch/run_build.sh

# common/builder, common/screener
CWE_BUILD_TEMPLATE=$CWE_COMMON/builder/TASK-BUILD-PROMPT-v1.md
CWE_BUILD_PREPARE=$CWE_COMMON/builder/build_prepare.py
CWE_SCREENER_PROMPT=$CWE_COMMON/screener/SCREENER-PROMPT-v2.md
CWE_SCREENER_RUNNER=$CWE_COMMON/screener/run_screener.py
CWE_SCREENER_RECORDS=$CWE_DATA_ROOT/common/screener/records

# common/gate
CWE_GATE=$CWE_COMMON/gate/gate.py
CWE_GATE_ONE=$CWE_COMMON/gate/gate_one_ds.sh
CWE_DOCKER_TUNING=$CWE_COMMON/gate/docker-tuning.env

# common/blindfix
CWE_RUN_BLINDFIX=$CWE_COMMON/blindfix/run_blindfix.sh
CWE_BLIND_BRIEF=$CWE_COMMON/blindfix/BLIND-FIX-BRIEF.md

# common/trial
CWE_TRIAL=$CWE_COMMON/trial/trial.py
CWE_TRIAL_STATE=$CWE_COMMON/trial/trial_state.py
CWE_TRIAL_SET=$CWE_COMMON/trial/trial_set.sh
CWE_TRIAL_SUMMARY=$CWE_COMMON/trial/trial_summary.py
CWE_RUN_TRIAL=$CWE_COMMON/trial/run_trial.sh

# common/audit
CWE_POSTMORTEM=$CWE_COMMON/audit/postmortem.py
CWE_AUDIT_RESULTS=$CWE_COMMON/audit/audit_results.py

# common/queue (work queue: docs/WORK-QUEUE.md)
CWE_CWEQ=$CWE_COMMON/queue/cweq.py

# common/fairness, common/versioning, common/util
CWE_FAIRNESS_BRIEF=$CWE_COMMON/fairness/FAIRNESS-REVIEW-BRIEF.md
CWE_FAIRNESS_VERDICT=$CWE_COMMON/fairness/fairness_verdict.py
CWE_SNAPSHOT=$CWE_COMMON/versioning/snapshot_experiment.sh
CWE_RESTORE=$CWE_COMMON/versioning/restore_snapshot.sh
CWE_AGENT_STATUS=$CWE_COMMON/util/agent_status.py
CWE_EVIDENCE=$CWE_COMMON/util/evidence.py
