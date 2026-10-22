#!/usr/bin/env bash
# Run one hidden group with the project's own Node test runner (tsx loads the
# TypeScript sources through the `source` export condition) and write JUnit XML.
set -u
group=$1
out=$2
cd /workspace/ghost/core || exit 1
exec node --conditions=source --import tsx --test \
  --test-reporter=junit --test-reporter-destination="$out" \
  "test/ghost-ds/$group"/*.test.js
