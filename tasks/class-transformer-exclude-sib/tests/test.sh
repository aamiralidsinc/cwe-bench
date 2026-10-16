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

# The hidden tests import the library source in /app as 'class-transformer'
# (see /tests/jest.config.js) and use the jest/ts-jest installed in /app.
cd /tmp
export APP_DIR=/app
for group in security functional; do
  JEST_JUNIT_OUTPUT_DIR=/logs/verifier/$group JEST_JUNIT_OUTPUT_NAME=results.xml \
    /app/node_modules/.bin/jest -c /tests/jest.config.js --ci --no-cache \
      --reporters=default --reporters=/opt/junit/node_modules/jest-junit \
      "/tests/$group/"
done

python3 /tests/score.py
