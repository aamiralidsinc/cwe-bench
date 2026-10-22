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
# The hidden tests run from a pristine copy outside the repo (/tests is read-only and the agent may
# have edited anything under /app). vitest and the workspace packages resolve through the repo's
# test project (/app/test/node_modules), as the repo's own tests do.
APP=/app
WORK=/tmp/verifier-tests
# Build the packages under test from the source in /app, the way the repo's own build does (type
# errors do not block the output; the tests decide).
cd "$APP"
for p in builder-util-runtime builder-util electron-publish electron-updater; do
    rm -rf "packages/$p/out"
    node_modules/.bin/tsc -p "packages/$p" --noEmitOnError false > "/logs/verifier/build-$p.log" 2>&1 || true
done
rm -rf "$WORK" && mkdir -p "$WORK"
cp -r /tests/. "$WORK"/
rm -rf "$WORK/node_modules"
ln -s "$APP/test/node_modules" "$WORK/node_modules"
cd "$WORK"
export CI=true NO_COLOR=1 FORCE_COLOR=0 EB_APP_ROOT="$APP"
unset DEBUG
for group in security functional; do
    timeout 600 node "$APP/test/node_modules/vitest/vitest.mjs" run --config "$WORK/vitest.config.mjs" --root "$WORK" "$group/" \
        --reporter=default --reporter=junit --outputFile.junit="/logs/verifier/$group/results.xml" \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

python3 /tests/score.py
