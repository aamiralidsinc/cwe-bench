#!/bin/bash
# Verifier entry point. Injects the hidden Go test files into the package trees
# under /app, runs the security and functional groups separately against
# whatever source is in /app (driving the API-server handlers and library APIs
# directly, against in-memory Kubernetes fakes), writes JUnit XML into
# /logs/verifier/{security,functional}/, then scores. No network is used.

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
export GOTOOLCHAIN=local
export GOCACHE=/root/.cache/go-build
export PATH="$PATH:/go/bin:/usr/local/go/bin"
JUNIT=/go/bin/go-junit-report

# Inject the hidden tests into their packages (the agent cannot see or edit
# these; we always use the copies under /tests, never any test file in /app).
while IFS= read -r src; do
  rel="${src#/tests/harness/}"
  dest="/app/${rel}"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
done < <(find /tests/harness -name '*.go')

PKGS="./server/sync/... ./server/workflowtemplate/... ./server/clusterworkflowtemplate/... ./server/auth/webhook/... ./workflow/artifacts/logging/... ./workflow/controller/..."

cd /app

# Security group: each test asserts the attack is blocked.
go test -p 2 -count=1 -run 'TestSecZZ' $PKGS -v 2>&1 | "$JUNIT" > /logs/verifier/security/results.xml

# Functional group: each test asserts legitimate behaviour still works.
go test -p 2 -count=1 -run 'TestFuncZZ' $PKGS -v 2>&1 | "$JUNIT" > /logs/verifier/functional/results.xml

python3 /tests/score.py
