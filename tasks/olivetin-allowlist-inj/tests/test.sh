#!/bin/bash
# Verifier entry point. Runs the hidden Go tests against /app and writes JUnit
# XML into /logs/verifier/{security,functional}/, then scores. Test files under
# /app are never trusted: the hidden suites and shared helpers are copied from
# /tests into the product package immediately before running.

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

PKG=/app/service/internal/executor

# --- remove any test files the agent may have left, then copy the hidden suites ---
rm -f "$PKG"/zz_hidden_*_test.go
cp -f /tests/support/zsupport_test.go     "$PKG/zz_hidden_support_test.go"
cp -f /tests/security/sec_inject_test.go  "$PKG/zz_hidden_security_test.go"
cp -f /tests/functional/func_legit_test.go "$PKG/zz_hidden_functional_test.go"

cd /app/service

# --- EDIT: the two groups. Each must write JUnit XML; neither aborts the other. ---
go test ./internal/executor/ -run '^TestSec_' -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > /logs/verifier/security/results.xml

go test ./internal/executor/ -run '^TestFunc_' -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > /logs/verifier/functional/results.xml

python3 /tests/score.py
