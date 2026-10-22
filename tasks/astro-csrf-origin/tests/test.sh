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
# The hidden tests import the compiled package (dist/), so rebuild `astro` from the solver's
# source first; a stale dist/ must never be graded, so it is removed before the build.
PKG=/app/packages/astro
H="$PKG/test-hidden"
cd "$PKG"
rm -rf "$PKG/dist"
if ! timeout 600 pnpm run build:ci > /logs/verifier/build.log 2>&1; then
    echo "astro build failed; see /logs/verifier/build.log"
    tail -40 /logs/verifier/build.log
fi

# Pristine copies of the tests and their helpers (the agent may have edited anything under /app).
rm -rf "$H" && mkdir -p "$H/units/security" "$H/units/functional"
cp -r /tests/support/units/. "$H/units/"
cp /tests/security/*.test.ts "$H/units/security/"
cp /tests/functional/*.test.ts "$H/units/functional/"
cp -r /tests/functional/project/. "$H/units/"
export NO_COLOR=1 FORCE_COLOR=0

run_group() {  # <group> <files...>
    local group="$1"; shift
    timeout 600 node --test --test-concurrency=1 --test-timeout=120000 \
        --test-reporter=junit --test-reporter-destination="/logs/verifier/$group/results.xml" \
        --test-reporter=spec --test-reporter-destination=stdout \
        "$@" 2>&1 | tee "/logs/verifier/$group.log" || true
}
run_group security "$H"/units/security/*.test.ts
run_group functional "$H"/units/functional/*.test.ts \
    "$H"/units/hono/*.test.ts "$H"/units/fetch/*.test.ts \
    "$H"/units/actions/*.test.ts "$H"/units/middleware/*.test.ts
rm -rf "$H"

python3 /tests/score.py
