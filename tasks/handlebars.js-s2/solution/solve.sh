#!/bin/bash
# Reference fix: the published change (validate every value the document contributes to the
# generated code at the compiler boundary) plus the two maintained sinks added to this copy
# (whole-number literal text and partial indentation).
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
