#!/usr/bin/env bash
# Functional group: legitimate DAG-API use, legitimate sync, and the project's own tests for the
# affected packages, all run with the project's native runner.
set -u
out="$1"
{
  go test ./internal/service/frontend/api/v1/ -run '^TestFunc' -count=1 -v 2>&1
  go test ./internal/persis/filedag/ ./internal/core/ ./internal/gitsync/ -count=1 -v 2>&1
} | go-junit-report -set-exit-code > "$out"
