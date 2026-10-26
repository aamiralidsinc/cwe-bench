#!/bin/bash
# Runs one hidden group with the project's native Go runner and writes JUnit XML.
#   run_suite.sh security|functional <out.xml>
# The hidden suites live in /workspace/zz_hidden and are named TestSecuritySuite /
# TestFunctionalSuite. The functional group also runs the project's own tests for the
# packages touched by the fix.
set -u
mode=$1
out=$2

export LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC
export GOTOOLCHAIN=local GOFLAGS=-mod=mod CGO_ENABLED=1 \
       GOMODCACHE=/go/pkg/mod GOCACHE=/go/cache

run() { # <go test args...>
  ( cd /workspace && go test "$@" -count=1 -v ) 2>&1
}

{
  if [ "$mode" = "security" ]; then
    run ./zz_hidden -run '^TestSecuritySuite$'
  else
    run ./zz_hidden -run '^TestFunctionalSuite$'
    # Project tests for the affected area. Three upstream tests assert the pre-fix
    # authorisation model (a request acts for a DID with no controller key present);
    # they are skipped because the fixed model rejects that request by design.
    run ./x/bonds/keeper ./x/claims/keeper ./x/entity/keeper ./x/iid/ante ./x/entity/ante ./app/apptesting \
        -skip 'TestKeeperTestSuite/(TestMsgEditBond.*|TestMsgUpdateBondState_AugmentedHatchToOpen|TestMsgUpdateEntity)$'
  fi
} | go-junit-report -set-exit-code > "$out"
