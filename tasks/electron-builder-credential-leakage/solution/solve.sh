#!/bin/bash
# Reference fix: the upstream fix (22a7532b, source files only) plus the fix for the pre-existing
# route it leaves open (redirected requests of the block-based update download, which Electron
# would follow with the original headers).
set -euo pipefail
cd /app
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
