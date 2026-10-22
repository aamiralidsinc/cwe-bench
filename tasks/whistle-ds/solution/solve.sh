#!/bin/bash
# Reference fix: the background component accepts only requests carrying its own
# internal credential on every entry path, and the panel establishes who is calling
# before it reads a host file or forwards an operator action to the component.
# Source changes only.
set -euo pipefail
cd /workspace
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
