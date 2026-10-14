#!/bin/bash
# Verifier entry point. Builds the hidden test harness against whatever russh
# source is in /app (the agent's code), runs the two groups through russh's
# real public client/server transport API, and writes JUnit XML into
# /logs/verifier/{security,functional}/, then scores.
#
# The harness crate is baked into the image at /opt/harness (the agent cannot
# modify it; it only edits /app). Its dependencies are pre-compiled in the
# image, so only /app/russh (and the tiny harness) recompile here. No network.
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

export CARGO_NET_OFFLINE=1
export CARGO_TERM_COLOR=never
HARNESS=/opt/harness
JUNIT="$HARNESS/target/nextest/ci/junit.xml"

cd "$HARNESS" || exit 1

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
rm -f "$JUNIT"
cargo nextest run --offline --profile ci -E 'binary(security)' >/dev/null 2>&1
cp -f "$JUNIT" /logs/verifier/security/results.xml 2>/dev/null

rm -f "$JUNIT"
cargo nextest run --offline --profile ci -E 'binary(functional)' >/dev/null 2>&1
cp -f "$JUNIT" /logs/verifier/functional/results.xml 2>/dev/null

python3 /tests/score.py
