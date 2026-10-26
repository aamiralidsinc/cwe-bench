#!/bin/bash
# Runs one hidden group over the affected packages (root/module aware) and writes JUnit XML.
#   run_suite.sh security|functional <out.xml>
# Every package is driven with the project's native runner. The hidden security tests are named
# TestSec_*, the hidden functional tests TestFunc_*; the project's own restored tests are the rest.
set -u
mode=$1
out=$2

export LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC
export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=0 \
       GOMODCACHE=/go/pkg/mod GOCACHE=/go/cache

pkgdirs=(
  sdk/trace
  sdk/metric
  exporters/zipkin
  exporters/otlp/otlptrace
  exporters/otlp/otlptrace/otlptracehttp
  exporters/otlp/otlptrace/otlptracegrpc
  exporters/otlp/otlplog/otlploghttp
)

run() { # <package dir> <go test args...>
  local d=$1
  shift
  ( cd "/workspace/$d" && go test . "$@" -count=1 -v ) 2>&1
}

{
  if [ "$mode" = "security" ]; then
    for d in "${pkgdirs[@]}"; do
      run "$d" -run '^TestSec_'
    done
  else
    for d in "${pkgdirs[@]}"; do
      run "$d" -run '^TestFunc_'
      # The project's own tests for the area, pristine copies restored by test.sh. One upstream
      # metric test skips itself when the global MeterProvider is not the one under test; it is
      # excluded rather than counted as an inconclusive result.
      run "$d" -skip '^(TestSec|TestFunc)_|^TestManualReaderInstrumentation$'
    done
  fi
} | go-junit-report -set-exit-code >"$out"
