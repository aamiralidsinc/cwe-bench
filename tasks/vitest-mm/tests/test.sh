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
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 CI=true NO_COLOR=1 FORCE_COLOR=0

# Rebuild the packages the agent may have changed, so the runner API and the
# browser/UI sources the tests exercise reflect the agent's fix.
( cd "$APP" && timeout 420 pnpm --filter vitest --filter @vitest/browser --filter @vitest/ui run build ) \
    > /logs/verifier/build.log 2>&1 || true

# Grade with the pristine runner copied when the image was built
# (/opt/vitest-verifier), not with the runner the agent just rebuilt, so the
# agent's changes cannot affect test collection or the JUnit reporter. The
# hidden tests sit inside that copy so bare imports (vitest, birpc, flatted,
# ws) resolve to it; the verifier config maps the product surfaces under test
# (vitest/node, the browser command sources, the preview provider) to /app.
VROOT=/opt/vitest-verifier
VERIFY="$VROOT/packages/vitest/__verifier__"
rm -rf "$VERIFY" "$APP/packages/vitest/__verifier__"
mkdir -p "$VERIFY"
cp -r /tests/security /tests/functional /tests/support "$VERIFY"/
cp /tests/vitest.verifier.config.ts "$VROOT/vitest.verifier.config.ts"

VITEST="$VROOT/packages/vitest/vitest.mjs"
for group in security functional; do
    ( cd "$VROOT" && VERIFIER_APP="$APP" VGROUP="$group" timeout 420 node "$VITEST" run \
        --config "$VROOT/vitest.verifier.config.ts" --root "$VROOT" \
        --reporter=default --reporter=junit \
        --outputFile.junit="/logs/verifier/$group/results.xml" ) \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
