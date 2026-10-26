#!/bin/bash
# Native runner for one hidden group. Invoked as `agent` by /tests/test.sh with the group name
# and an agent-writable directory for the JUnit XML. Every suite runs through the project's own
# vitest configuration inside the restored tree; a failing suite never stops the next one.
set -u
group="${1:?usage: run-group.sh <security|functional> <outdir>}"
out="${2:?usage: run-group.sh <security|functional> <outdir>}"
mkdir -p "$out"

ROOT="${ROOT:-/workspace}"
export TEST_ENV=server-side
export DB_DIALECT=sqlite
export DB_STORAGE="${TMPDIR:-/tmp}/nocobase-verify.sqlite"
export DB_TEST_PREFIX=verify_
export LOGGER_LEVEL=error
export NODE_ENV=test

FM=packages/plugins/@nocobase/plugin-file-manager/src/server/__tests__/__verifier__
CORE=packages/core/server/src/__tests__/__verifier__

run() {  # <test path> <report name>
  local file="$1" name="$2"
  (
    cd "$ROOT" || exit 1
    node ./node_modules/vitest/vitest.mjs --run --poolOptions.threads.singleThread=true \
      --reporter=junit --outputFile="$out/$name.xml" "$file"
  ) >"$out/$name.log" 2>&1 || true
}

case "$group" in
  security)
    run "$FM/fm-storage-security.test.ts" fm-storage-security
    run "$CORE/pm-security.test.ts" pm-security
    ;;
  functional)
    run "$FM/fm-storage-functional.test.ts" fm-storage-functional
    run "$CORE/pm-functional.test.ts" pm-functional
    ;;
  *)
    echo "unknown group: $group" >&2
    exit 2
    ;;
esac

exit 0
