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
mkdir -p /app/tests

# Security: hidden behavioural tests through the public API.
cp /tests/security/sec_hubuum.rs /app/tests/sec_hubuum.rs
cd /app
cargo test --offline --locked --features blocking --test sec_hubuum -- --test-threads=1 \
    > /logs/verifier/security/cargo.log 2>&1
python3 /tests/junit.py /logs/verifier/security/cargo.log \
    /logs/verifier/security/results.xml security

# Functional: hidden legitimate-use tests.
cp /tests/functional/fun_hubuum.rs /app/tests/fun_hubuum.rs
cargo test --offline --locked --features blocking --test fun_hubuum -- --test-threads=1 \
    > /logs/verifier/functional/cargo.log 2>&1
python3 /tests/junit.py /logs/verifier/functional/cargo.log \
    /logs/verifier/functional/results.xml functional

# The project's own tests for the affected area, run from pristine copies that
# overwrite whatever is in /app.
cp /tests/functional/project/foundations.rs /app/tests/foundations.rs
cargo test --offline --locked --features blocking,typed-schemas --lib \
    errors::tests::exposes_structured_api_error_response -- --exact --test-threads=1 \
    > /logs/verifier/functional/project_errors.log 2>&1
python3 /tests/junit.py /logs/verifier/functional/project_errors.log \
    /logs/verifier/functional/project_errors.xml project_errors
cargo test --offline --locked --features blocking,typed-schemas --test foundations \
    response_and_error_debug_output_redacts_sensitive_values -- --exact \
    > /logs/verifier/functional/project_foundations.log 2>&1
python3 /tests/junit.py /logs/verifier/functional/project_foundations.log \
    /logs/verifier/functional/project_foundations.xml project_foundations

python3 /tests/score.py
