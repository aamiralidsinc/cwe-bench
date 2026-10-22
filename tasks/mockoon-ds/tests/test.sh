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
cd /app

# Rebuild the shared libraries from the source the agent left, so the wrappers
# (which import the built package) see the same code the tests import.
npm run build:commons >/dev/null 2>&1 || true
npm run build:commons-server >/dev/null 2>&1 || true

# The hidden suites live outside /app; copy fresh copies in for this run only.
rm -rf /app/.hidden-tests
mkdir -p /app/.hidden-tests
cp -a /tests/support /app/.hidden-tests/support
cp -a /tests/security /app/.hidden-tests/security
cp -a /tests/functional /app/.hidden-tests/functional

# Security: management access requires the configured token, browser origins
# are not granted by default, transaction credentials are redacted, and
# environment-variable writes stay inside the configured prefix.
node --import tsx --test --test-concurrency=1 \
  --test-reporter=junit --test-reporter-destination=/logs/verifier/security/results.xml \
  ".hidden-tests/security/*.test.ts" >/dev/null 2>&1 || true

# Functional: legitimate use keeps working (mock routes and their CORS,
# management endpoints with the token, streams, runtime logging, serverless).
node --import tsx --test --test-concurrency=1 \
  --test-reporter=junit --test-reporter-destination=/logs/verifier/functional/results.xml \
  ".hidden-tests/functional/*.test.ts" >/dev/null 2>&1 || true

python3 /tests/score.py
