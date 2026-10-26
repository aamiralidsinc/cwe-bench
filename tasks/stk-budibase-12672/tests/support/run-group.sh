#!/usr/bin/env bash
# Hidden verifier runner: runs the selected jest files for one group and writes
# a JUnit XML report. Invoked from tests/test.sh as `bash run-group.sh <group> <out.xml>`.
set -u
GROUP="${1:?group}"
OUT="${2:?out}"
WS=/workspace
SUP="$WS/.htests/support"
TMP="$(mktemp -d)"
JEST="$WS/node_modules/.bin/jest"
export NODE_OPTIONS="--no-node-snapshot"

run_jest() {
  local cfg="$1"
  local json="$2"
  shift 2
  ( cd "$WS" && "$JEST" --config "$cfg" --runInBand --ci --forceExit \
      --json --outputFile="$json" --runTestsByPath "$@" ) >>"$TMP/jest.log" 2>&1 || true
}

case "$GROUP" in
  security)
    run_jest "$SUP/jest.server.config.js" "$TMP/security-server.json" \
      "$WS/packages/server/src/integrations/tests-ds/zz_sec_origin.test.ts" \
      "$WS/packages/server/src/threads/tests-ds/zz_sec_runner.test.ts" \
      "$WS/packages/server/src/sdk/workspace/oauth2/tests-ds/zz_sec_oauth2.test.ts"
    ;;
  functional)
    run_jest "$SUP/jest.server.config.js" "$TMP/functional-server.json" \
      "$WS/packages/server/src/integrations/tests-ds/zz_func_origin.test.ts" \
      "$WS/packages/server/src/integrations/tests-ds/zz_func_outbound.test.ts" \
      "$WS/packages/server/src/threads/tests-ds/zz_func_runner.test.ts" \
      "$WS/packages/server/src/threads/query.spec.ts" \
      "$WS/packages/server/src/sdk/workspace/queries/queries.spec.ts"
    run_jest "$SUP/jest.backendcore.config.js" "$TMP/functional-backendcore.json" \
      "$WS/packages/backend-core/src/utils/tests/outboundFetch.spec.ts"
    ;;
  *)
    echo "unknown group: $GROUP" >&2
    ;;
esac

cp "$TMP/jest.log" /tmp/run-group.log 2>/dev/null || true
python3 -I "$SUP/jest2junit.py" "$OUT" "$TMP"/*.json
