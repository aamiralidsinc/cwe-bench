#!/bin/bash
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_DOCKER_TUNING" 2>/dev/null || true
# run_pipeline.sh <deepseek|mimo> <slug>
# One candidate, end to end, model-driven generation + both-target trial:
#   build (driver) -> gate (nop/oracle/patches) -> if sound, trial BOTH targets -> ledger.
# Fairness/blind-fix are deferred to tasks that come back both-fail (validated separately).
set -uo pipefail
D=${1:?driver}; S=${2:?slug}
R="$CWE_ROOT"; cd "$R" || exit 1
LED="$CWE_SIBLING_OUT/pipeline/ledger_$D.tsv"
LOG="build/$S/pipeline.log"
mkdir -p "build/$S"
# Atomic claim: only one pipeline instance ever processes a slug, so extra run_lane
# workers / a re-launch at higher concurrency can share the same list without collision.
if ! mkdir "build/$S/.lockdir" 2>/dev/null; then exit 0; fi
# Already started by another (possibly pre-lock) instance? Leave it strictly alone.
if [ -f "build/$S/pipeline.log" ]; then exit 0; fi
# Each slug is built exactly once per lane: start the task tree clean.
rm -rf "tasks/$S"
[ -f "$LED" ] || echo -e "utc\tslug\tstage\toutcome\tdeepseek\tmimo" > "$LED"
log(){ printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$S" "$1" "$2" "${3:-}" "${4:-}" >> "$LED"; }

echo "=== $(date -u +%FT%TZ) build $S (driver=$D) ===" >> "$LOG"
"$CWE_DRIVE" "$D" bash "$CWE_RUN_BUILD" "$S" >> "$LOG" 2>&1
tf=$(find "tasks/$S" -type f 2>/dev/null | wc -l | tr -d ' ')
bx=$(cat "build/$S/build-exit.txt" 2>/dev/null || echo '-')
# A builder cut off by a quota/API error/timeout produced no verdict on the candidate, and a
# half-built task must not be gated (it would read as "unsound"). Until 2026-10-20 a quota stop
# was logged exactly like a real build failure.
st=$(python3 "$CWE_AGENT_STATUS" "build/$S/build-run.json" "${bx//-/1}" --details "build/$S/build_status.json")
if [ "$st" != ok ]; then log build "BUILD-INCOMPLETE (agent did not finish: $st; tf=$tf; not a candidate verdict)"; exit 0; fi
if [ "$tf" -lt 5 ]; then log build "stopped/failed: agent finished but left tf=$tf task files (exit=$bx)"; exit 0; fi

# The gate (nop/oracle/patches) and its retry policy live in one place: gate_one_ds.sh retries
# only infrastructure errors, never task failures, and leaves exactly one of .sound / .unsound /
# .gate_error (see its header). Its one-line result goes to the ledger.
res=$(bash "$CWE_GATE_ONE" "$S" 2>>"$LOG"); rc=$?
echo "gate: $res" >> "$LOG"
case $rc in
  0) : ;;
  1) log gate "UNSOUND (task failure: ${res#"$S "})"; exit 0 ;;
  *) log gate "GATE-ERROR (infra/internal, not a task verdict: ${res#"$S "})"; exit 0 ;;
esac
# Build+gate only. Trials are run per-stage by common/trial/trial_set.sh (see pipelines/sibling/archive/batch1-lane-pilot/QUEUE.md).
log gate "sound"
echo "=== $S BUILT + SOUND (ready to trial) $(date -u +%FT%TZ) ===" >> "$LOG"
