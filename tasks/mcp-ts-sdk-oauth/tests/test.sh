#!/bin/bash
# Verifier entry point. Runs the hidden vitest suites against the SDK source in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.

# Stop the agent before grading. On an agent timeout Harbor stops waiting for the agent but
# does not kill it inside this shared container; in round 1 it kept editing /app while the
# tests ran (15 runs). Kill every Claude Code process first. Do not remove this block.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# Run the hidden tests from a pristine copy outside the repo (/tests is read-only and the agent
# may have edited anything under /app). vitest and the SDK's third-party dependencies resolve
# through the client package's installed node_modules; the SDK itself is the source in /app.
APP=/app
VITEST="$APP/packages/client/node_modules/vitest/vitest.mjs"
WORK=/tmp/verifier-tests
rm -rf "$WORK" && mkdir -p "$WORK"
cp -r /tests/. "$WORK"/
rm -rf "$WORK/node_modules"
ln -s "$APP/packages/client/node_modules" "$WORK/node_modules"
cd "$WORK"
export CI=true NO_COLOR=1 FORCE_COLOR=0 MCP_APP_ROOT="$APP"

# Each group runs in its own process; a failure in one must not stop the other.
for group in security functional; do
    timeout 600 node "$VITEST" run --config "$WORK/vitest.config.mjs" --root "$WORK" "$group/" \
        --reporter=default --reporter=junit --outputFile.junit="/logs/verifier/$group/results.xml" \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
