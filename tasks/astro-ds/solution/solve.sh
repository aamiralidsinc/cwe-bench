#!/bin/bash
# Reference fix: the upstream fix (0b30b35f, source files only) plus the same origin check at every
# request-handling building block that can dispatch without the middleware chain (the composable
# action, form-action, page/endpoint, endpoint-only, fragment and rewrite steps).
set -euo pipefail
cd /workspace
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
