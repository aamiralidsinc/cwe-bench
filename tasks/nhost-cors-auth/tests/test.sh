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
export GOFLAGS=-mod=vendor GOPROXY=off GOTOOLCHAIN=local CGO_ENABLED=0
export GOPATH=/go GOCACHE=/root/.cache/go-build GIN_MODE=release
export PATH="$PATH:/go/bin:/usr/local/go/bin"
JUNIT=/go/bin/go-junit-report

# Copy the hidden tests into the tree, and restore the project's own tests for
# the area from pristine copies (never trust test files in /app).
copy_tree() {
  local base="$1" src rel
  while IFS= read -r src; do
    rel="${src#"$base"/}"
    mkdir -p "/app/$(dirname "$rel")"
    cp "$src" "/app/$rel"
  done < <(find "$base" -path "$base/project" -prune -o -name '*.go' -print)
}
rm -rf /app/cli/cmd/configserver/zzlocalserve
rm -f /app/cli/cmd/configserver/logsapi/*_test.go /app/internal/lib/oapi/middleware/*_test.go
copy_tree /tests/functional/project
copy_tree /tests/security
copy_tree /tests/functional

cd /app
HIDDEN=./cli/cmd/configserver/zzlocalserve
PROJECT="./cli/cmd/configserver/logsapi ./internal/lib/oapi/middleware"

# Security group: foreign browser origins get no access to the local
# configuration service, and no response carries a stored secret value.
go test -p 2 -count=1 -timeout 400s -run '^TestSec' $HIDDEN -v 2>&1 | "$JUNIT" > /logs/verifier/security/results.xml

# Functional group: the local dashboard keeps working, plus the project's own tests.
go test -p 2 -count=1 -timeout 500s -skip '^TestSec' $HIDDEN $PROJECT -v 2>&1 | "$JUNIT" > /logs/verifier/functional/results.xml

python3 /tests/score.py
