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

# The hidden suites import the embed plugin source in /app through the '@product' alias
# (see /tests/jest.config.js) and run it on a jsdom document, using the jest in /app.
export APP_DIR=/app
export NODE_PATH=/opt/junit/node_modules
JEST=/app/node_modules/.bin/jest
CFG=/tests/jest.config.js
for group in security functional; do
  JEST_JUNIT_OUTPUT_DIR="/logs/verifier/$group" JEST_JUNIT_OUTPUT_NAME=results.xml \
    "$JEST" -c "$CFG" --ci --no-cache --runInBand --rootDir "/tests/$group" 2>&1 | tail -n 40 || true
done

python3 /tests/score.py
