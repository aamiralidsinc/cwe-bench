#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests, with the pristine runner copied into the image
# at /opt/vitest-verifier when it was built.
#
# The product under test is the agent's tree: the verifier config aliases
# `vitest/node` and `@vitest/browser-preview` to /app, so the rebuilt packages
# are what the tests exercise, while collection and reporting come from the
# pristine runner and cannot be influenced by the agent.

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

APP=/app
VERIFIER=/opt/vitest-verifier
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 CI=true NO_COLOR=1 FORCE_COLOR=0

# Rebuild the two packages the agent may have changed. Fail closed: if the
# rebuild does not succeed, no tests are run and score.py reports 0 rather
# than silently grading a stale dist that may not contain the fix.
if ! ( cd "$APP" && timeout 420 pnpm --filter vitest --filter @vitest/browser run build ) \
        > /logs/verifier/build.log 2>&1; then
    echo "product rebuild failed; nothing to grade" >&2
    python3 /tests/score.py
    exit $?
fi

# Place the hidden tests inside the pristine runner's vitest package tree so
# bare imports resolve exactly as the repo's own tests do. The runner's
# node_modules is linked to /app/node_modules in the image.
rm -rf "$VERIFIER/packages/vitest/__verifier__"
mkdir -p "$VERIFIER/packages/vitest/__verifier__"
cp -r /tests/security /tests/functional /tests/support "$VERIFIER/packages/vitest/__verifier__/"
cp /tests/vitest.verifier.config.ts "$VERIFIER/vitest.verifier.config.ts"

VITEST="$VERIFIER/packages/vitest/vitest.mjs"
for group in security functional; do
    VERIFIER_APP="$APP" VGROUP="$group" timeout 420 node "$VITEST" run \
        --config "$VERIFIER/vitest.verifier.config.ts" --root "$VERIFIER" \
        --reporter=default --reporter=junit \
        --outputFile.junit="/logs/verifier/$group/results.xml" \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
