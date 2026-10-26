#!/bin/bash
# Reference fix: a compiled-rules blob is accepted only when it is consistent
# with the invariants the compiler establishes, so malformed ids, offsets,
# text literals and per-pattern tables are refused before the rules are used.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
