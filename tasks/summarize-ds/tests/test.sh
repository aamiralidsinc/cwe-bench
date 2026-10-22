#!/bin/bash
# Verifier entry point. Runs the hidden vitest suites against the product source in /app
# and the project's own tests for the affected area, writes JUnit XML into
# /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run only the
# copies under /tests.

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

# Offline name-resolution table shared by the behavioural tests and by the project's own
# tests (idempotent; the container runs as root). The verifier setup also serves it over a
# local DNS server, so resolution strategies that do not use getaddrinfo see it too.
while read -r _ip _name; do
  case "${_ip:-}" in ""|"#"*) continue ;; esac
  grep -qE "^[[:space:]]*${_ip}[[:space:]]+${_name}([[:space:]]|$)" /etc/hosts || echo "${_ip} ${_name}" >> /etc/hosts
done < /tests/hosts.list

# Hidden behavioural tests, from a pristine copy outside the repo.
WORK=/tmp/verifier-tests
rm -rf "$WORK" && mkdir -p "$WORK"
cp -r /tests/. "$WORK"/
rm -rf "$WORK/node_modules"
ln -s /app/node_modules "$WORK/node_modules"
cd "$WORK" || exit 1

# Each group runs in its own process; a failure in one must not stop the other.
for group in security functional; do
    APP_DIR=/app timeout 700 node /app/node_modules/vitest/vitest.mjs run \
        --config "$WORK/vitest.config.mts" --root "$WORK" "$group/" \
        --reporter=default --reporter=junit \
        --outputFile.junit="/logs/verifier/$group/results.xml" \
        2>&1 | tee "/logs/verifier/$group.log" || true
done

# The project's own tests for the affected area, restored from pristine copies over
# whatever the agent left in /app/tests, so they exercise the agent's product edits.
cp /tests/functional/project/transcript.podcast-provider.pristine.ts /app/tests/transcript.podcast-provider.test.ts
cp /tests/functional/project/transcript.podcast-provider.podcast-transcript.pristine.ts /app/tests/transcript.podcast-provider.podcast-transcript.test.ts
cp /tests/functional/project/transcript.podcast-provider.paths-coverage.pristine.ts /app/tests/transcript.podcast-provider.paths-coverage.test.ts
cp /tests/functional/project/daemon.url-fetch-guard.pristine.ts /app/tests/daemon.url-fetch-guard.test.ts
( cd /app && timeout 600 node node_modules/vitest/vitest.mjs run \
    --reporter=default --reporter=junit \
    --outputFile.junit=/logs/verifier/functional/project.xml \
    tests/transcript.podcast-provider.test.ts \
    tests/transcript.podcast-provider.podcast-transcript.test.ts \
    tests/transcript.podcast-provider.paths-coverage.test.ts \
    tests/daemon.url-fetch-guard.test.ts \
    2>&1 | tee /logs/verifier/project.log ) || true

python3 /tests/score.py
