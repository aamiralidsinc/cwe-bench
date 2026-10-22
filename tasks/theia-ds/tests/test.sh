#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
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

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
# The hidden tests load the compiled package output. Rebuild the affected
# projects so the solver's source changes are what the tests run. Type errors
# still emit JavaScript (noEmitOnError is false), and a compile failure must not
# stop the two groups.
cd /app
/app/node_modules/.bin/tsc --build \
    packages/ai-ide packages/ai-chat packages/ai-terminal \
    packages/ai-anthropic packages/ai-copilot >/tmp/tsc-verifier.log 2>&1 || true

cd /tmp
export NODE_PATH=/app/node_modules
for group in security functional; do
  export JUNIT_OUTPUT=/logs/verifier/$group/results.xml
  /app/node_modules/.bin/mocha --exit --no-config --timeout 10000 \
    --require ignore-styles \
    --require reflect-metadata/Reflect \
    --require @theia/test-setup \
    --require /tests/support/setup.js \
    --reporter /tests/support/junit-reporter.js \
    "/tests/$group"
done

python3 /tests/score.py
