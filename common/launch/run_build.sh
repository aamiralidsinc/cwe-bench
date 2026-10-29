#!/bin/bash
# Launch one headless Claude Code builder for a prepared task. Transparent: it runs the builder
# with --permission-mode bypassPermissions (a build needs Bash+Docker+Go autonomously on this
# dedicated VM). Usage: common/launch/run_build.sh SLUG   Env: MODEL (default claude-opus-5-5), BUILD_TIMEOUT
# (default 18000 s = 5 h since 2026-10-26; 3 h before: under a shared gate cap 28 of 43 scale-batch-2 builds hit 3 h).
#
#   run_build.sh SLUG --resume SESSION --msg-file FILE   continue a builder session (pipelines/sibling/6-build/
#                                                         resume_pipeline.sh): FILE is the operator's message;
#                                                         stamps resume_start_utc.txt instead of start_utc.txt
#
# Since 2026-10-28 (four builders killed by name searches that matched the brief on their command line):
#   - the brief (or the resume message) goes in on stdin, never in the arguments;
#   - the builder carries CWE_BUILD_RUN=<slug>:<epoch>:<pid> and CWE_BUILD_SLUG in its environment, inherited by every
#     process it starts: common/util/build_procs.py finds a build's processes by it (orphan guard, after-build sweep),
#     and common/gate/gate.py runs a builder's gate stages in the builder lane (static and nop only);
#   - the brief names the release this launcher runs from: the "Project root" that build_prepare.py recorded (the
#     release active when the prompt was made) is replaced at launch (builders ran gate.py from an old release);
#   - after the builder exits, every process still carrying its tag is stopped (build_procs.py sweep);
#   - CWE_BUILD_PIDNS=1 (off by default): the builder runs in its own PID namespace (sudo unshare, then back to this
#     user), so a name-based kill inside cannot reach other jobs and everything it started ends with it. Falls back
#     to a plain launch, with a log line, when sudo -n, unshare or setpriv is missing.
# start_utc.txt / resume_start_utc.txt, build-exit.txt and end_utc.txt are written here only (builders never write them).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
SLUG=${1:?usage: run_build.sh SLUG [--resume SESSION --msg-file FILE]}; shift
SESS=""; MSGF=""
while [ $# -gt 0 ]; do
  case "$1" in
    --resume) SESS=${2:?--resume needs a session id}; shift 2 ;;
    --msg-file) MSGF=${2:?--msg-file needs a file}; shift 2 ;;
    *) echo "run_build.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done
cd "$CWE_ROOT" || exit 1
WORK="$HOME/.tb-graders/cwe/work/$SLUG"; mkdir -p "$WORK/.launch"
STAMP=$(date -u +%Y%m%dT%H%M%SZ); BRIEF="$WORK/.launch/brief-$STAMP.md"
if [ -n "$SESS" ]; then
  [ -s "$MSGF" ] || { echo "$SLUG: no resume message (--msg-file)"; exit 2; }
  cp "$MSGF" "$BRIEF"
  START=resume_start_utc.txt; RESUME=(--resume "$SESS")
else
  # The brief with its project root set to this release (the old one stays readable but is not the one in use).
  python3 -I - "build/$SLUG/BUILD-PROMPT.md" "$CWE_ROOT" "$BRIEF" <<'PY' || exit 1
import re, sys
src, root, out = sys.argv[1:4]
text = open(src, encoding="utf-8").read()
m = re.search(r"Project root: `([^`]+)`", text)
if m and m.group(1) != root:
    text = text.replace(m.group(1), root)
    print(f"brief: project root {m.group(1)} -> {root}")
open(out, "w", encoding="utf-8").write(text)
PY
  START=start_utc.txt; RESUME=()
fi
TOKEN="$SLUG:$(date -u +%s):$$"
cwe_stamp "build/$SLUG" "$START"

# The builder command, with the build tag in its environment (not exported: this script and the sweep stay untagged).
builder=(env CWE_BUILD_RUN="$TOKEN" CWE_BUILD_SLUG="$SLUG"
         timeout "${BUILD_TIMEOUT:-18000}" "$HOME/.local/bin/claude" -p ${RESUME[@]+"${RESUME[@]}"}
         --model "${MODEL:-claude-opus-5-5}" --permission-mode bypassPermissions
         --add-dir "$CWE_ROOT" --add-dir "$HOME/.tb-graders/cwe/work"
         --output-format json)
if [ "${CWE_BUILD_PIDNS:-0}" = 1 ]; then
  if sudo -n -E true 2>/dev/null && command -v unshare >/dev/null && command -v setpriv >/dev/null; then
    echo "$SLUG: builder in its own PID namespace"
    builder=(sudo -n -E unshare --pid --fork --mount-proc --kill-child --
             setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups --
             env PATH="$PATH" HOME="$HOME" "${builder[@]}")
  else
    echo "$SLUG: CWE_BUILD_PIDNS=1 but sudo -n -E, unshare or setpriv is unavailable: plain launch"
  fi
fi
"${builder[@]}" < "$BRIEF" > "build/$SLUG/build-run.json" 2> "build/$SLUG/build-run.err"
rc=$?; echo "$rc" | cwe_write_atomic "build/$SLUG/build-exit.txt"
cwe_stamp "build/$SLUG" end_utc.txt
python3 -I "$CWE_COMMON/util/build_procs.py" sweep "$TOKEN"
echo "$SLUG: builder exit $(cwe_read "build/$SLUG" build-exit.txt)"
