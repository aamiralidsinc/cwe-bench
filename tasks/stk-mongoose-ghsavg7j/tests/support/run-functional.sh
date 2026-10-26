#!/usr/bin/env bash
# Functional group: the hidden keep-working suite plus the project's own suites for the
# affected area. Each run writes its own JUnit XML; they are merged into the single file the
# grader expects. A run that writes no XML is a verifier defect, not a scored zero.
set -u

OUT="$1"
SUPPORT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${MONGOOSE_ROOT:?}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

run() {  # <name> <mocha args...>
  local name="$1"; shift
  rm -f "$TMP/$name.xml"
  "$ROOT/node_modules/.bin/mocha" --no-config --exit --timeout 30000 \
    --reporter xunit --reporter-option "output=$TMP/$name.xml" "$@" >/dev/null 2>&1 || true
  [ -s "$TMP/$name.xml" ] || { echo "missing JUnit XML for $name" >&2; exit 1; }
}

run hidden "$ROOT/.htests/functional/keep-working.test.js"
run helper "$ROOT/test/helpers/query.sanitizeFilter.test.js"
run query "$ROOT/test/query.test.js" --grep 'sanitizeFilter|\$where'

python3 -I "$SUPPORT/junit-merge.py" "$OUT" \
  "$TMP/hidden.xml" "$TMP/helper.xml" "$TMP/query.xml"
