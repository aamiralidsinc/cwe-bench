#!/bin/bash
# Verifier entry point. Runs the hidden Go tests against /app and writes JUnit
# XML into /logs/verifier/{security,functional}/, then scores. Test files under
# /app are never trusted: the pristine project test files, the project testdata,
# and the hidden suites are all restored/copied from /tests before running.

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

export GOTOOLCHAIN=go1.26.3 GOEXPERIMENT=jsonv2 GOFLAGS=-mod=mod CGO_ENABLED=0

PKG=/app/pkg/plugin

# --- restore pristine project tests + testdata (defeat any edits in /app) ---
rm -rf "$PKG/testdata"
cp -r /tests/pristine/testdata "$PKG/testdata"
cp -f /tests/pristine/manager_test.go      "$PKG/manager_test.go"
cp -f /tests/pristine/manager_unix_test.go "$PKG/manager_unix_test.go"
cp -f /tests/pristine/index_test.go        "$PKG/index_test.go"

# --- copy the hidden suites into the product package ---
cp -f /tests/support/*.go     "$PKG/"
cp -f /tests/security/*.go     "$PKG/"
cp -f /tests/functional/*.go   "$PKG/"

cd /app

# --- EDIT: the two groups. Each must write JUnit XML; neither aborts the other. ---
go test ./pkg/plugin/ -run '^TestSec_' -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > /logs/verifier/security/results.xml

go test ./pkg/plugin/ -run '^(TestFunc_|TestManager_Uninstall|TestManager_Information|TestManager_LoadAll|TestManager_Run)' -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > /logs/verifier/functional/results.xml

python3 /tests/score.py
