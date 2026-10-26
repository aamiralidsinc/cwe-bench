#!/bin/bash
# Run the project's own unit specs against the submitted sources and always write a JUnit
# XML document to stdout, so a submission that cannot be loaded or whose specs cannot start
# is scored as a failure rather than reported as a verifier defect.
set -u
cd /workspace || exit 1

fallback() {
  printf '%s\n' \
    '<?xml version="1.0" encoding="UTF-8"?>' \
    '<testsuite name="project specs" tests="1" failures="1" errors="0" skipped="0">' \
    '<testcase classname="project" name="the submitted project runs its own specs"><failure>the submitted project could not be loaded or its specs could not start</failure></testcase>' \
    '</testsuite>'
}

if ! node -e "require('/workspace/lib')" >/dev/null 2>&1; then
  fallback
  exit 0
fi

out=$(mktemp) || { fallback; exit 0; }
./node_modules/.bin/mocha --require ./spec/env/node.js --reporter xunit \
  spec/basic.js spec/blocks.js spec/partials.js spec/string-params.js \
  spec/track-ids.js spec/security.js spec/ast.js spec/whitespace-control.js \
  spec/subexpressions.js spec/data.js spec/strict.js spec/precompiler.js \
  spec/helpers.js spec/regressions.js spec/runtime.js > "$out" 2>/dev/null
rc=$?
if grep -q '<testsuite' "$out"; then
  cat "$out"
else
  fallback
fi
rm -f "$out"
exit $rc
