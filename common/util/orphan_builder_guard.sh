#!/bin/bash
# orphan_builder_guard.sh [interval_s] : stop builder agents that outlive their build (2026-10-26).
#
# Seen in scale batch 1: a builder ran `kill -9` on a list of PIDs that included its own launcher
# (common/launch/run_build.sh). The pipeline then saw the build as finished and started the post-build
# checks while the builder, now orphaned (parent PID 1), kept working and killed those checks twice
# (stk-glance-ghsavwr9, exit 137).
#
# Every interval (default 60 s): a `claude` process whose arguments carry the build prompt of task <slug>
# ("Build one security-fix benchmark task" ... "Task: `<slug>`") is stopped, with its child processes, when
# build/<slug>/end_utc.txt exists (the pipeline has recorded the build as ended). Blind-fix, listing,
# fairness and trial agents have other prompts and are never touched. Log: build/audit/orphan_builder_guard.log
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
IV=${1:-60}; LOG=build/audit/orphan_builder_guard.log
echo "$(date -u +%FT%TZ) guard start (every ${IV}s)" >> "$LOG"
while true; do
  for p in $(pgrep -x claude 2>/dev/null) $(pgrep -f '/bin/claude -p' 2>/dev/null); do
    a=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null) || continue
    case "$a" in *"Build one security-fix benchmark task"*) ;; *) continue ;; esac
    slug=$(printf '%s' "$a" | grep -o 'Task: `[^`]*`' | head -1 | sed 's/Task: `//; s/`//')
    [ -n "$slug" ] && [ -f "build/$slug/end_utc.txt" ] || continue
    # Only a builder that started BEFORE the recorded end is an orphan (a rebuild leaves an older end_utc.txt).
    pstart=$(date -d "$(ps -o lstart= -p "$p" 2>/dev/null)" +%s 2>/dev/null) || continue
    bend=$(date -d "$(cat "build/$slug/end_utc.txt")" +%s 2>/dev/null) || continue
    [ "$pstart" -lt "$bend" ] || continue
    kids=$(pgrep -P "$p" | tr '\n' ' ')
    kill -TERM "$p" $kids 2>/dev/null; sleep 3; kill -9 "$p" $kids 2>/dev/null
    echo "$(date -u +%FT%TZ) stopped orphaned builder of $slug (pid $p, build ended $(cat build/$slug/end_utc.txt))" >> "$LOG"
  done
  sleep "$IV"
done
