#!/bin/bash
# Reference fix: the upstream fix (edd12e28, source files only) plus the fixes for the two
# pre-existing gaps the cwe-bench version adds (standalone refresh / code-exchange helpers,
# and tokens returned by the standalone helpers without their authorization-server binding).
set -euo pipefail
cd /app
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
