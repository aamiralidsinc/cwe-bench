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

# The hidden suites drive the product through its real public API and the CLI
# code generator, so they reflect the agent's edits directly. Copy them to a
# scratch directory first so nothing under /app can influence collection.
APP=/app
TESTROOT=/tmp/verifier-tests
rm -rf "$TESTROOT"
mkdir -p "$TESTROOT"
cp -r /tests/security /tests/functional /tests/support "$TESTROOT"/

export APP
export NODE_PATH="$APP/node_modules${NODE_PATH:+:$NODE_PATH}"

OUT=/logs/verifier/security/results.xml timeout 300 node "$TESTROOT/security/run.js" \
    2>&1 | tee /logs/verifier/security.log || true
OUT=/logs/verifier/functional/results.xml timeout 600 node "$TESTROOT/functional/run.js" \
    2>&1 | tee /logs/verifier/functional.log || true

python3 /tests/score.py
