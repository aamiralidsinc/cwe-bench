#!/bin/bash
# Verifier entry point. Runs the hidden Go tests against /app and writes JUnit
# XML into /logs/verifier/{security,functional}/, then scores. Test files under
# /app are never trusted: the hidden suites and the project's own tests are
# restored/copied from /tests before running.

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

export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=0

# --- copy the hidden suites into their product packages ---
cp -f /tests/security/pki/*.go /app/builtin/logical/pki/
cp -f /tests/security/ssh/*.go /app/builtin/logical/ssh/
cp -f /tests/security/acl/*.go /app/vault/external_tests/policy/
cp -f /tests/functional/pki/*.go /app/builtin/logical/pki/
cp -f /tests/functional/ssh/*.go /app/builtin/logical/ssh/
cp -f /tests/functional/acl/*.go /app/vault/external_tests/policy/

cd /app

# --- EDIT: the two groups. Each must write JUnit XML; neither aborts the other. ---
run_group() {
  local outdir="$1"; shift
  local runre="$1"; shift
  local pkg
  for pkg in "$@"; do
    local tag
    tag=$(echo "$pkg" | tr '/.' '__')
    go test "$pkg" -run "$runre" -count=1 -v 2>&1 \
      | go-junit-report -set-exit-code > "$outdir/${tag}.xml" || true
  done
}

run_group /logs/verifier/security   '^TestSec_' \
  ./builtin/logical/pki/ ./builtin/logical/ssh/ ./vault/external_tests/policy/

run_group /logs/verifier/functional '^TestFunc_' \
  ./builtin/logical/pki/ ./builtin/logical/ssh/ ./vault/external_tests/policy/

# The project's own tests for the affected area. They are restored from pristine
# copies shipped under /tests (the agent may have edited /app). They exercise the
# agent's product edits, not edited tests.
cp -f /tests/functional/project/identitytpl_templating_test.go /app/sdk/helper/identitytpl/templating_test.go
cp -f /tests/functional/project/policy_acl_test.go             /app/vault/policy/acl_test.go
cp -f /tests/functional/project/policy_policy_test.go          /app/vault/policy/policy_test.go

( cd /app/sdk && go test ./helper/identitytpl/ -count=1 -v 2>&1 \
    | go-junit-report -set-exit-code > /logs/verifier/functional/project_identitytpl.xml || true )
go test ./vault/policy/ -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > /logs/verifier/functional/project_policy.xml || true

python3 /tests/score.py
