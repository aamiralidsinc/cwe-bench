#!/bin/bash
# precision_validation copy of run_build.sh (2026-10-22): paths only (project root = this folder; CLAUDE_BIN override).
# Launch one headless Claude Code builder for a prepared task. Transparent: it runs the builder
# with --permission-mode bypassPermissions (a build needs Bash+Docker+Go autonomously on this
# dedicated VM). Usage: run_build.sh SLUG   Env: MODEL (default claude-opus-5-5), BUILD_TIMEOUT.
set -uo pipefail
SLUG=$1
PV_ROOT=${PV_ROOT:-$(cd "$(dirname "$0")" && pwd)}
cd "$PV_ROOT" || exit 1
mkdir -p "$HOME/.tb-graders/cwe/work/$SLUG"
PROMPT=$(cat "build/$SLUG/BUILD-PROMPT.md")
date -u +%FT%TZ > "build/$SLUG/start_utc.txt"
timeout "${BUILD_TIMEOUT:-10800}" "${CLAUDE_BIN:-$HOME/.local/bin/claude}" -p "$PROMPT" \
  --model "${MODEL:-claude-opus-5-5}" --permission-mode bypassPermissions \
  --add-dir "$PV_ROOT" --add-dir "$HOME/.tb-graders/cwe/work" \
  --output-format json > "build/$SLUG/build-run.json" 2> "build/$SLUG/build-run.err"
echo $? > "build/$SLUG/build-exit.txt"
date -u +%FT%TZ > "build/$SLUG/end_utc.txt"
echo "$SLUG: builder exit $(cat build/$SLUG/build-exit.txt)"
