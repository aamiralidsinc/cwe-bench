#!/bin/bash
# Verifier entry point. Builds the hidden test harness against whatever russh
# source is in /app (the agent's code), runs the two groups through russh's
# real public client/server transport API, and writes JUnit XML into
# /logs/verifier/{security,functional}/, then scores.
#
# The harness crate is baked into the image at /opt/harness (the agent cannot
# modify it; it only edits /app). Its dependencies are pre-compiled in the
# image, so only /app/russh (and the tiny harness) recompile here. No network.

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

export CARGO_NET_OFFLINE=1
export CARGO_TERM_COLOR=never
HARNESS=/opt/harness
JUNIT="$HARNESS/target/nextest/ci/junit.xml"

cd "$HARNESS" || exit 1
# The hidden harness sources arrive with /tests at grading time; the image holds
# only empty stubs (the agent shares this container). cp refreshes mtimes, so
# cargo rebuilds the harness from these real sources.
mkdir -p src tests
cp -f /tests/harness/src/lib.rs src/lib.rs
cp -f /tests/harness/tests/security.rs /tests/harness/tests/functional.rs tests/

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
rm -f "$JUNIT"
cargo nextest run --offline --no-fail-fast --profile ci -E 'binary(security)' >/dev/null 2>&1
cp -f "$JUNIT" /logs/verifier/security/results.xml 2>/dev/null

rm -f "$JUNIT"
cargo nextest run --offline --no-fail-fast --profile ci -E 'binary(functional)' >/dev/null 2>&1
cp -f "$JUNIT" /logs/verifier/functional/results.xml 2>/dev/null

python3 /tests/score.py
