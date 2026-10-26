#!/bin/bash
# Runs one hidden group with the project's native Go test runner and writes JUnit XML.
#   run_suite.sh security|functional <out.xml>
set -u
mode=$1
out=$2

export LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC
export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=0 \
       GOMODCACHE=/go/pkg/mod GOCACHE=/go/cache

cd /workspace || exit 1
if [ "$mode" = "security" ]; then
  go test ./hidden_security -run '^TestSec_' -count=1 -v 2>&1
else
  go test ./hidden_functional -run '^TestFunc_' -count=1 -v 2>&1
fi | go-junit-report -set-exit-code >"$out"
