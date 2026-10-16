#!/bin/bash
# Verifier entry point. Rebuilds the Cloudreve server from whatever is in /app,
# starts it against a fresh local (sqlite + in-memory) backend, then drives the
# security and functional test groups against the running server over its real
# HTTP API, writing JUnit XML into /logs/verifier/{security,functional}/ and
# scoring. The authoritative tests live under /tests; copies in /app are ignored.

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

export GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local CGO_ENABLED=0

# Rebuild from /app (offline, incremental against the baked module/build cache).
if ! ( cd /app && go build -p 2 -o /usr/local/bin/cloudreve . ); then
    echo "WARNING: build of cloudreve from /app failed" >&2
fi

# Stop any server left over from a previous invocation in the same container.
pkill -f 'cloudreve server' 2>/dev/null
sleep 1

# Fresh, writable run dir so each run starts from an empty database.
RUN=/run/cr
rm -rf "$RUN"; mkdir -p "$RUN"
cp /usr/local/bin/cloudreve "$RUN/cloudreve" 2>/dev/null
( cd "$RUN" && exec ./cloudreve server >/tmp/cloudreve.log 2>&1 ) &
SRV=$!

# Wait for the API to come up.
up=0
for _ in $(seq 1 60); do
    if curl -sf -o /dev/null http://127.0.0.1:5212/ 2>/dev/null; then up=1; break; fi
    sleep 1
done
[ "$up" = 1 ] || { echo "server did not come up"; tail -40 /tmp/cloudreve.log >&2; }

# Register the admin first so it becomes user id 1 (the admin account); the
# tests then log in as this user. Harmless if it already exists.
curl -s -X POST http://127.0.0.1:5212/api/v4/user \
     -H 'Content-Type: application/json' \
     -d '{"email":"admin@cloudreve.test","password":"Passw0rd!"}' >/dev/null 2>&1

# --- run the two groups; a failure in one must not stop the other.
python3 -m pytest /tests/security   -q -p no:cacheprovider -o cache_dir=/tmp/pc_s \
    --junitxml=/logs/verifier/security/results.xml
python3 -m pytest /tests/functional -q -p no:cacheprovider -o cache_dir=/tmp/pc_f \
    --junitxml=/logs/verifier/functional/results.xml

kill "$SRV" 2>/dev/null

python3 /tests/score.py
