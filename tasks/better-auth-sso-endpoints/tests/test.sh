#!/bin/bash
# Verifier entry point. Runs the hidden vitest suites against the @better-auth/sso source in
# /app and writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run only the copies
# under /tests.

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

# Place the hidden tests inside the sso package tree so bare imports (better-auth,
# oauth2-mock-server) resolve through that package's installed node_modules, exactly as the
# repo's own tests do. The product itself (@better-auth/sso) is aliased to the source in /app
# by the verifier config, so the agent's edits are what gets tested.
APP=/app
VERIFY="$APP/packages/sso/__verifier__"
rm -rf "$VERIFY"
mkdir -p "$VERIFY"
cp -r /tests/security /tests/functional /tests/support "$VERIFY"/
cp /tests/support/vitest.verifier.config.mjs "$APP/vitest.verifier.config.mjs"

VITEST="$APP/node_modules/vitest/vitest.mjs"
export CI=true NO_COLOR=1 FORCE_COLOR=0

# Each group runs in its own process; a failure in one must not stop the other (no `set -e`).
for group in security functional; do
    timeout 600 node "$VITEST" run \
        --config "$APP/vitest.verifier.config.mjs" --root "$APP" \
        "packages/sso/__verifier__/$group/" \
        --reporter=default --reporter=junit \
        --outputFile.junit="/logs/verifier/$group/results.xml" \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
