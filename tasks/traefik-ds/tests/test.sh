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
export GOFLAGS=-mod=mod GOTOOLCHAIN=local CGO_ENABLED=0
export GOPATH=/go GOCACHE=/root/.cache/go-build
export PATH="$PATH:/go/bin:/usr/local/go/bin"
JUNIT=/go/bin/go-junit-report

# Copy the hidden tests into their packages, and restore the project's own
# tests for the area from pristine copies (never trust test files in /app).
copy_tree() {
  local base="$1" src rel
  while IFS= read -r src; do
    rel="${src#"$base"/}"
    mkdir -p "/app/$(dirname "$rel")"
    cp "$src" "/app/$rel"
  done < <(find "$base" -path "$base/project" -prune -o -name '*.go' -print)
}
copy_tree /tests/functional/project
copy_tree /tests/security
copy_tree /tests/functional

PKGS="./pkg/middlewares/auth ./pkg/middlewares/headers ./pkg/middlewares/passtlsclientcert ./pkg/middlewares/trustedheaders ./pkg/server ./pkg/config/static"
cd /app

# Security group: a client must not be able to spoof a header that Traefik sets
# or strips, and the entry-point underscore setting must hold.
go test -p 2 -count=1 -timeout 300s -run '^TestSecZZ' $PKGS -v 2>&1 | "$JUNIT" > /logs/verifier/security/results.xml

# Functional group: the hidden feature tests plus the project's own tests.
go test -p 2 -count=1 -timeout 600s -skip '^TestSecZZ' $PKGS -v 2>&1 | "$JUNIT" > /logs/verifier/functional/results.xml

python3 /tests/score.py
