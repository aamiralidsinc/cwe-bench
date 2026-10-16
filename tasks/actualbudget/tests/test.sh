#!/bin/bash
# Verifier entry point. Runs the two test groups (vitest + supertest) against
# the Actual sync-server source in /app and writes JUnit XML into
# /logs/verifier/{security,functional}/, then scores.
#
# The tests and their config are taken only from /tests (never from /app, which
# the agent may have edited). /tests is read-only and vite needs to write a temp
# file next to its config, so we copy the trusted tests to a writable location
# and run from there.

# Stop the agent before grading (2026-10-16). On an agent timeout Harbor stops waiting for the
# agent but does not kill it inside this shared container, and it was seen editing /app while
# the tests ran (research/own-runs; build/postmortem.py). Kill every Claude Code process first.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

T=/tmp/verifier-tests
rm -rf "$T"
cp -r /tests "$T"

cd /app/packages/sync-server
export NODE_ENV=test
export NO_COLOR=1
export NODE_OPTIONS="--experimental-vm-modules --import ./register-loader.mjs"
VITEST=./node_modules/.bin/vitest

# Each group runs in its own process; a failure in one must not stop the other.
"$VITEST" --run --config "$T/vitest.security.mjs"   || true
"$VITEST" --run --config "$T/vitest.functional.mjs" || true

python3 /tests/score.py
