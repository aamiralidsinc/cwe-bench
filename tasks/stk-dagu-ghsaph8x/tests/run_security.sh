#!/usr/bin/env bash
# Security group: the hidden confinement tests, run with the project's native runner.
set -u
out="$1"
go test ./internal/service/frontend/api/v1/ -run '^TestSec' -count=1 -v 2>&1 \
  | go-junit-report -set-exit-code > "$out"
