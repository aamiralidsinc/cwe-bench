#!/bin/bash
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_DOCKER_TUNING" 2>/dev/null || true
# resume_pipeline.sh <slug> <build|gate> [session-id]
# Resumes one sibling2 task frozen during the 2026-10-24 Docker deadlock, without a rebuild:
#   build -> `claude --resume <session>` (same conversation, fresh time budget), then the normal gate;
#   gate  -> re-run the gate only (no model tokens).
# Same post-build checks, gate call and ledger format as pipelines/sibling/6-build/run_pipeline.sh.
set -uo pipefail
S=${1:?slug}; STAGE=${2:?build|gate}; SESS=${3:-}
R="$CWE_ROOT"; cd "$R" || exit 1
LED="pipelines/sibling/out/pipeline/ledger_deepseek.tsv"; LOG="build/$S/pipeline.log"
mkdir "build/$S/.resume_lock" 2>/dev/null || exit 0
log(){ printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$S" "$1" "$2" "${3:-}" "${4:-}" >> "$LED"; }
echo "=== $(date -u +%FT%TZ) RESUME $S stage=$STAGE session=${SESS:-none} ===" >> "$LOG"

if [ "$STAGE" = build ]; then
  [ -n "$SESS" ] || { log build "RESUME-ERROR (no session id)"; exit 0; }
  for f in build-run.json build-run.err build-exit.txt; do [ -f "build/$S/$f" ] && mv "build/$S/$f" "build/$S/$f.pre-resume"; done
  MSG="Note from the operator: this build was paused for about an hour while we fixed a host Docker bug (the system Docker daemon was deadlocking under load; it is fixed and restarted now). Containers that were running before the pause were stopped, and any private dockerd started during this session was shut down. Use the system Docker only; do not start your own dockerd. Continue the task from where you left off and finish it as the original brief says."
  "$CWE_DRIVE" deepseek bash -c '
    date -u +%FT%TZ > "build/'"$S"'/resume_start_utc.txt"
    timeout "${BUILD_TIMEOUT:-10800}" "$HOME/.local/bin/claude" -p "$0" --resume "'"$SESS"'" \
      --model "$MODEL" --permission-mode bypassPermissions \
      --add-dir "'"$CWE_ROOT"'" --add-dir "$HOME/.tb-graders/cwe/work" \
      --output-format json > "build/'"$S"'/build-run.json" 2> "build/'"$S"'/build-run.err"
    echo $? > "build/'"$S"'/build-exit.txt"; date -u +%FT%TZ > "build/'"$S"'/end_utc.txt"' "$MSG" >> "$LOG" 2>&1
  tf=$(find "tasks/$S" -type f 2>/dev/null | wc -l | tr -d ' ')
  bx=$(cat "build/$S/build-exit.txt" 2>/dev/null || echo '-')
  st=$(python3 "$CWE_AGENT_STATUS" "build/$S/build-run.json" "${bx//-/1}" --details "build/$S/build_status.json")
  if [ "$st" != ok ]; then log build "BUILD-INCOMPLETE (resumed; agent did not finish: $st; tf=$tf; not a candidate verdict)"; exit 0; fi
  if [ "$tf" -lt 5 ]; then log build "stopped/failed: resumed agent finished but left tf=$tf task files (exit=$bx)"; exit 0; fi
fi

res=$(bash "$CWE_GATE_ONE" "$S" 2>>"$LOG"); rc=$?
echo "gate (resumed): $res" >> "$LOG"
case $rc in
  0) log gate "sound" ; echo "=== $S BUILT + SOUND (resumed) $(date -u +%FT%TZ) ===" >> "$LOG" ;;
  1) log gate "UNSOUND (task failure: ${res#"$S "})" ;;
  *) log gate "GATE-ERROR (infra/internal, not a task verdict: ${res#"$S "})" ;;
esac
