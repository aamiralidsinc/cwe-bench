#!/bin/bash
# Reference fix: gate the internal request-serving component so it only acts on
# requests carrying its own internal credential (the header the UI layer already
# sends), and resolve stored-item handles through the shared helper. Source
# changes only.
set -euo pipefail
cd /app
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
