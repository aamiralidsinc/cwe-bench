#!/bin/sh
# Runs the project's own suite (its offline cases) and writes JUnit XML to $1.
set -u
OUT="$1"
WORK="${PROJECT_TEST_DIR:-/workspace/.htests}"
JSON="$WORK/jest-report.json"
rm -f "$JSON" "$OUT"
node "${VERIFIER_NODE_MODULES:-/opt/verifier/node_modules}/jest/bin/jest.js" \
  --config "$WORK/jest.config.js" --ci --runInBand --json --outputFile "$JSON" \
  --testNamePattern 'Basic parsing|gracefully' > "$WORK/jest.log" 2>&1
node "$WORK/convert-jest.js" "$JSON" "$OUT"
