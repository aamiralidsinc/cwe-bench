#!/usr/bin/env bash
# Run one hidden group as the unprivileged agent and write a single JUnit XML to $2.
# Usage: run-group.sh <security|functional> <output.xml>
set -u
group=${1:?group}
out=${2:?output}
cd /workspace || exit 1

case "$group" in
  security)
    node --test --test-concurrency=1 --test-reporter=junit \
      --test-reporter-destination="$out" .htests/security/*.test.mjs
    rc=$?
    ;;
  functional)
    node --test --test-concurrency=1 --test-reporter=junit \
      --test-reporter-destination="$out.node.xml" .htests/functional/*.test.mjs
    rc1=$?
    ./node_modules/.bin/mocha --no-config --no-package \
      --require ./test-helpers/node-env.js --reporter xunit \
      --reporter-options output="$out.project.xml" test
    rc2=$?
    python3 -I /workspace/.htests/runner/merge-junit.py \
      "$out.node.xml" "$out.project.xml" "$out"
    rc=$((rc1 != 0 || rc2 != 0))
    ;;
  *)
    echo "unknown group $group" >&2
    exit 2
    ;;
esac

exit "$rc"
