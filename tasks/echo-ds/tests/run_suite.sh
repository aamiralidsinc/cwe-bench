#!/bin/bash
# Runs one hidden group with the project's native runner and writes JUnit XML.
#   run_suite.sh security|functional <out.xml>
# The hidden security tests are named TestSec_*, the hidden functional tests TestFunc_*; the
# pristine project tests restored by test.sh are the middleware package's static-area tests.
set -u
mode=$1
out=$2

export LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC
export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=0 \
       GOMODCACHE=/go/pkg/mod GOCACHE=/go/cache

run() { # <package> <go test args...>
  ( cd /workspace && go test "$@" -count=1 -v ) 2>&1
}

{
  if [ "$mode" = "security" ]; then
    run . -run '^TestSec_'
  else
    run . -run '^TestFunc_'
    # The project's own tests for the affected area, restored pristine by test.sh.
    run ./middleware -run '^(TestStatic|TestMustStaticWithConfig|TestFormat)'
  fi
} | go-junit-report -set-exit-code > "$out"
