#!/bin/bash
# Verifier entry point. Rebuilds rclone from whatever is in /app, then runs the
# security and functional test groups against a real `rclone serve s3` process
# over HTTP, writing JUnit XML into /logs/verifier/{security,functional}/ and
# scoring. The authoritative test sources live under /tests and are overlaid
# onto the pre-built harness crate so the agent's copies in /app are not used.

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

export GOFLAGS=-mod=mod
export GOPROXY=off
export GOTOOLCHAIN=local

HARNESS=/opt/harness

# Use the uploaded (authoritative) test sources, not any baked/edited copies.
cp /tests/lib/s3test.go                  "$HARNESS/s3test/s3test.go"
cp /tests/lib/authproxy.go               "$HARNESS/authproxy/main.go"
cp /tests/security/security_test.go      "$HARNESS/security/security_test.go"
cp /tests/functional/functional_test.go  "$HARNESS/functional/functional_test.go"

# Rebuild rclone from /app (offline, incremental using the baked module/build
# cache). Only the packages the solver changed recompile.
if ! ( cd /app && go build -o /usr/local/bin/rclone . ); then
    echo "WARNING: rclone build from /app failed" >&2
    rm -f /usr/local/bin/rclone
fi
# Rebuild the auth-proxy helper from its authoritative source.
( cd "$HARNESS/authproxy" && go build -o /usr/local/bin/authproxy . ) \
    || echo "WARNING: authproxy build failed" >&2

run_group() {
    # $1 = package/group name (security|functional), $2 = output dir
    local group="$1" outdir="$2"
    ( cd "$HARNESS" && go test -count=1 -json "./$group/" ) \
        >"/tmp/${group}.json" 2>"/tmp/${group}.err"
    cat "/tmp/${group}.err" >&2
    python3 /tests/lib/gojson2junit.py "/tmp/${group}.json" "$group" \
        >"${outdir}/results.xml"
}

# --- EDIT: run the two groups. Each writes JUnit XML; a failure in one must
# --- not stop the other (no `set -e`).
run_group security  /logs/verifier/security
run_group functional /logs/verifier/functional

python3 /tests/score.py
