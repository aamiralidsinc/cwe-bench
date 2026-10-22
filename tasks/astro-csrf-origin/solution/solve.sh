#!/bin/bash
# Reference fix: the upstream fix (0b30b35f, source files only). The origin check moves into a
# shared predicate that the action dispatch and the composable page/endpoint dispatch also apply.
set -euo pipefail
cd /app
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
