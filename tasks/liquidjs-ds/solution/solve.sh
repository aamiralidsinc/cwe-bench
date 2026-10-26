#!/bin/bash
# Reference fix: enforce the own-property read restriction at the context boundary so every
# consumer of a supplied sequence (filters, iteration tags, printed output, loop metadata and
# programmatic lookups) sees own slots only, and make the end accessors and the structural size
# lookup restriction-aware while keeping set/map sizes and the disabled setting working.
set -euo pipefail
cd /workspace
FIX="$(dirname "$0")/fix.patch"
[ -f "$FIX" ] || FIX=/solution/fix.patch
patch -p1 < "$FIX"
