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
APP=/app
VROOT=/opt/verifier
RUN="$VROOT/run"

# The hidden suites live under /tests and import the product source through the
# '@app' alias (see /tests/vitest.config.ts). Copy them next to the verifier
# toolchain so bare imports (vitest) resolve, and run each group separately.
rm -rf "$RUN"
mkdir -p "$RUN"
cp -r /tests/security /tests/functional /tests/support "$RUN"/
cp /tests/vitest.config.ts "$RUN/vitest.config.ts"

for group in security functional; do
    ( cd "$RUN" && VERIFIER_APP="$APP" VGROUP="$group" timeout 600 \
        node "$VROOT/node_modules/vitest/vitest.mjs" run \
        --config "$RUN/vitest.config.ts" --root "$RUN" \
        --reporter=default --reporter=junit \
        --outputFile.junit="/logs/verifier/$group/results.xml" ) \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
