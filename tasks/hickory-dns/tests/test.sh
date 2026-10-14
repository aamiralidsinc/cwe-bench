#!/bin/bash
# Verifier entry point. Runs the hidden DNSSEC tests against whatever is in /app
# and writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# The authoritative test sources live under /tests; they are overlaid onto the
# pre-built harness crate so only the (possibly patched) /app crates recompile.
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

export CARGO_HOME=/opt/cargo
export CARGO_TARGET_DIR=/opt/target
export CARGO_NET_OFFLINE=true

HARNESS=/opt/harness

# Use the uploaded (authoritative) test sources, not the baked copies. Only
# copy when they actually differ, so an identical upload does not bump mtimes
# and force cargo to rebuild the pre-compiled test binaries.
sync_src() { cmp -s "$1" "$2" || cp "$1" "$2"; }
sync_src /tests/security/security.rs     "$HARNESS/tests/security.rs"
sync_src /tests/functional/functional.rs "$HARNESS/tests/functional.rs"

run_group() {
    # $1 = binary/group name (security|functional), $2 = output dir
    local group="$1" outdir="$2"
    # Clear any stale junit from a previous group so the find below is exact.
    find /opt/harness/target /opt/target -name junit.xml -delete 2>/dev/null
    # --no-fail-fast: every test must run so all cases land in the JUnit report.
    ( cd "$HARNESS" && cargo nextest run --profile ci --offline --no-fail-fast -E "binary(${group})" )
    local junit
    junit="$(find /opt/harness/target /opt/target -name junit.xml -print -quit 2>/dev/null)"
    if [ -n "$junit" ] && [ -f "$junit" ]; then
        cp "$junit" "${outdir}/results.xml"
    fi
}

# --- EDIT: run the two groups. Each writes JUnit XML; a failure in one must not
# --- stop the other (no `set -e`).
run_group security  /logs/verifier/security
run_group functional /logs/verifier/functional

python3 /tests/score.py
