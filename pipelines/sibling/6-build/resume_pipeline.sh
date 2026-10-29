#!/bin/bash
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
. "$CWE_DOCKER_TUNING" 2>/dev/null || true
# resume_pipeline.sh <slug> <build|gate> [session-id]   (RESUME_MSG_FILE or RESUME_MSG overrides the operator note)
# Resumes one sibling build without a rebuild (first for the tasks frozen in the 2026-10-24 Docker deadlock; since
# 2026-10-28 also for genuine 5-h timeouts and outside kills, after they are debugged; queue kind build_resume):
#   build -> the builder continues its own conversation (common/launch/run_build.sh --resume: the message goes in on
#            stdin, fresh time budget), then the normal post-build checks;
#   gate  -> the post-build checks only (no model tokens).
# The post-build checks are common/gate/postbuild.sh (gate + blind fix + blind patch check), as after a fresh build
# (pipelines/sibling/6-build/run_pipeline.sh); until 2026-10-28 a resume ran gate_one_ds.sh and got no blind check.
# Same ledger format as run_pipeline.sh. One resume of a task at a time (flock; the lock ends with this script).
set -uo pipefail
S=${1:?slug}; STAGE=${2:?build|gate}; SESS=${3:-}
R="$CWE_ROOT"; cd "$R" || exit 1
LED="$CWE_SIBLING_OUT/pipeline/ledger_deepseek.tsv"; LOG="build/$S/pipeline.log"
exec 7>"build/$S/.resume.lock"
flock -n 7 || { echo "$S: another resume holds build/$S/.resume.lock"; exit 0; }
# Ledger row, and the same line in pipeline.log (the build_resume job's outcome check reads it there).
log(){ printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$S" "$1" "$2" "${3:-}" "${4:-}" | tee -a "$LOG" >> "$LED"; }
echo "=== $(date -u +%FT%TZ) RESUME $S stage=$STAGE session=${SESS:-none} ===" >> "$LOG"

if [ "$STAGE" = build ]; then
  [ -n "$SESS" ] || { log build "RESUME-ERROR (no session id)"; exit 0; }
  sfx=pre-resume; [ -e "build/$S/build-exit.txt.pre-resume" ] && sfx="pre-resume-$(date -u +%Y%m%dT%H%M%SZ)"
  for f in build-run.json build-run.err build-exit.txt; do [ -f "build/$S/$f" ] && mv "build/$S/$f" "build/$S/$f.$sfx"; done
  MF="$HOME/.tb-graders/cwe/work/$S/.launch/resume-msg-$(date -u +%Y%m%dT%H%M%SZ).md"; mkdir -p "$(dirname "$MF")"
  if [ -n "${RESUME_MSG_FILE:-}" ] && [ -s "$RESUME_MSG_FILE" ]; then
    cp "$RESUME_MSG_FILE" "$MF"
  else
    printf '%s\n' "${RESUME_MSG:-Note from the operator: this build was paused for about an hour while we fixed a host Docker bug (the system Docker daemon was deadlocking under load; it is fixed and restarted now). Containers that were running before the pause were stopped, and any private dockerd started during this session was shut down. Use the system Docker only; do not start your own dockerd. Continue the task from where you left off and finish it as the original brief says.}" > "$MF"
  fi
  echo "resume message: $MF" >> "$LOG"
  # 7>&-: the builder and whatever it starts never hold this script's resume lock.
  "$CWE_DRIVE" deepseek bash "$CWE_RUN_BUILD" "$S" --resume "$SESS" --msg-file "$MF" >> "$LOG" 2>&1 7>&-
  tf=$(find "tasks/$S" -type f 2>/dev/null | wc -l | tr -d ' ')
  bx=$(cwe_read "build/$S" build-exit.txt || echo '-')
  st=$(python3 "$CWE_AGENT_STATUS" "build/$S/build-run.json" "${bx//-/1}" --details "build/$S/build_status.json")
  if [ "$st" != ok ]; then log build "BUILD-INCOMPLETE (resumed; agent did not finish: $st; tf=$tf; not a candidate verdict)"; echo "$S: builder exit $bx, BUILD-INCOMPLETE (resumed)"; exit 0; fi
  if [ "$tf" -lt 5 ]; then log build "stopped/failed: resumed agent finished but left tf=$tf task files (exit=$bx)"; echo "$S: builder exit $bx, stopped/failed (resumed)"; exit 0; fi
fi

# The post-build checks, exactly as after a fresh build (postbuild.sh also does the B2b file-time reset first).
bash "$CWE_COMMON/gate/postbuild.sh" "$S" >> "$LOG" 2>&1 7>&-; rc=$?
res="$S $(tail -1 "build/$S/postbuild.log" 2>/dev/null)"
echo "gate (resumed): $res" >> "$LOG"
case $rc in
  0) log gate "sound" ; echo "=== $S BUILT + SOUND (resumed) $(date -u +%FT%TZ) ===" >> "$LOG" ;;
  1) log gate "UNSOUND (task failure: ${res#"$S "})" ;;
  *) log gate "GATE-ERROR (infra/internal, not a task verdict: ${res#"$S "})" ;;
esac
echo "$S: builder exit $(cwe_read "build/$S" build-exit.txt || echo '-'), post-build exit $rc (resumed)"
