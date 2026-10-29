#!/bin/bash
# orphan_builder_guard.sh [interval_s] : stop builder agents that outlive their launcher (2026-10-26; parent check 2026-10-28).
#
# Seen in scale batch 1: a builder ran `kill -9` on a list of PIDs that included its own launcher
# (common/launch/run_build.sh). The pipeline then saw the build as finished and started the post-build
# checks while the builder, now orphaned (parent PID 1), kept working and killed those checks twice
# (stk-glance-ghsavwr9, exit 137).
#
# Every interval (default 60 s), one pass of `common/util/build_procs.py guard`: a builder whose launcher
# (run_build.sh, or resume_pipeline.sh for an older resume) is no longer among its ancestors is stopped with every
# process of its run. The launcher is checked, not build/<slug>/end_utc.txt alone: on 2026-10-28 the old rule stopped
# spring-data-mongodb-s2's live builder after it wrote end_utc.txt itself. Builders are found by the CWE_BUILD_RUN tag
# run_build.sh puts in their environment (older builders: the brief on their command line, plus the old end_utc rule).
# Blind-fix, listing, fairness and trial agents carry neither and are never touched.
# Log: build/audit/orphan_builder_guard.log
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
IV=${1:-60}; LOG=build/audit/orphan_builder_guard.log
echo "$(date -u +%FT%TZ) guard start (every ${IV}s; launcher check)" >> "$LOG"
while true; do
  python3 -I "$CWE_COMMON/util/build_procs.py" guard >> "$LOG" 2>&1
  sleep "$IV"
done
