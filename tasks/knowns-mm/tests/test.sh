#!/bin/bash
# Verifier entry point. Runs the hidden Go tests against /app and writes JUnit
# XML into /logs/verifier/{security,functional}/, then scores. Test files under
# /app are never trusted: the pristine project test files and the hidden suites
# are all restored/copied from /tests before running.

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

export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=1

# --- restore pristine project tests (defeat any edits or extras in /app) ----
for pair in "models:internal/models" "storage:internal/storage" \
            "handlers:internal/mcp/handlers" "routes:internal/server/routes"; do
  src="/tests/pristine/${pair%%:*}"
  dst="/app/${pair##*:}"
  rm -f "$dst"/*_test.go
  cp -f "$src"/*_test.go "$dst/"
done

# --- copy the hidden suites into the product packages ----------------------
cp -f /tests/support/handlers_support_test.go   /app/internal/mcp/handlers/
cp -f /tests/security/sec_doc_path_test.go      /app/internal/mcp/handlers/
cp -f /tests/security/sec_memory_id_test.go     /app/internal/mcp/handlers/
cp -f /tests/security/sec_template_name_test.go /app/internal/mcp/handlers/
cp -f /tests/security/sec_doc_archive_test.go   /app/internal/mcp/handlers/
cp -f /tests/security/sec_memory_history_test.go /app/internal/mcp/handlers/
cp -f /tests/security/sec_template_file_test.go /app/internal/server/routes/
cp -f /tests/functional/func_keep_working_test.go /app/internal/mcp/handlers/
cp -f /tests/functional/func_template_preview_test.go /app/internal/server/routes/

cd /app

# --- the two groups. Each must write JUnit XML; neither aborts the other. ---
go test ./internal/mcp/handlers/ ./internal/server/routes/ \
  -run 'TestSec_' -count=1 -v 2>&1 \
  | go-junit-report > /logs/verifier/security/results.xml

# Functional: the keep-working suite plus the project's own tests for the
# affected packages. The security tests are skipped here so a vulnerable tree
# still shows a clean functional run. The auto-archive sweeper tests are also
# skipped: they wait on a 3s wall-clock deadline and flake under load. They
# cover task retention, which this report does not touch.
go test ./internal/models/... ./internal/storage/... \
        ./internal/mcp/handlers/... ./internal/server/routes/... \
  -skip '^(TestSec_|TestTaskAutoArchiveSweeper)' -count=1 -v 2>&1 \
  | go-junit-report > /logs/verifier/functional/results.xml

python3 /tests/score.py
