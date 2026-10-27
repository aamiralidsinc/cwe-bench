#!/bin/bash
# Launch one headless Claude Code builder for a prepared task. Transparent: it runs the builder
# with --permission-mode bypassPermissions (a build needs Bash+Docker+Go autonomously on this
# dedicated VM). Usage: common/launch/run_build.sh SLUG   Env: MODEL (default claude-opus-5-5), BUILD_TIMEOUT
# (default 18000 s = 5 h since 2026-10-26; 3 h before: under a shared gate cap 28 of 43 scale-batch-2 builds hit 3 h).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_COMMON/markers.sh"     # marker helpers (common/markers.py, docs/STAGE-CONTRACTS.md)
SLUG=$1
cd "$CWE_ROOT" || exit 1
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
PROMPT=$(cat "build/$SLUG/BUILD-PROMPT.md")
cwe_stamp "build/$SLUG" start_utc.txt
timeout "${BUILD_TIMEOUT:-18000}" "$HOME/.local/bin/claude" -p "$PROMPT" \
  --model "${MODEL:-claude-opus-5-5}" --permission-mode bypassPermissions \
  --add-dir "$CWE_ROOT" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "build/$SLUG/build-run.json" 2> "build/$SLUG/build-run.err"
rc=$?; echo "$rc" | cwe_write_atomic "build/$SLUG/build-exit.txt"
cwe_stamp "build/$SLUG" end_utc.txt
echo "$SLUG: builder exit $(cwe_read "build/$SLUG" build-exit.txt)"
