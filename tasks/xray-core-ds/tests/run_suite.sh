#!/bin/bash
# Runs one hidden group over the affected packages and writes JUnit XML.
#   run_suite.sh security|functional <out.xml>
# The hidden security tests are named TestSec_*, the hidden functional tests TestFunc_*; the
# project's own restored tests for the area are the rest.
set -u
mode=$1
out=$2

export LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC
export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=0 \
       GOMODCACHE=/go/pkg/mod GOCACHE=/go/cache

pkgdirs=(
  transport/internet/grpc
  transport/internet/hysteria
  transport/internet/tcp
  transport/internet/finalmask/realm
  app/dns
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
    done
    # The project's own tests for the area that do not need the network.
    run transport/internet/tls -run '^(TestCertificateIssuing|TestExpiredCertificate|TestInsecureCertificates|TestCalculateCertHash|TestVerifyPeerLeafCert|TestVerifyPeerCACert)$'
    run transport/internet/grpc -run '^(TestConfig_GetServiceName|TestConfig_GetTunStreamName|TestConfig_GetTunMultiStreamName|TestSetUserAgent)$'
    run transport/internet/tcp -run '^TestGetOriginalDestination$'
  fi
} | go-junit-report -set-exit-code >"$out"
