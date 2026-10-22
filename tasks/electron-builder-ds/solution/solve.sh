#!/bin/bash
# Reference fix: drop every credential header on a cross-origin redirect (Node and Electron paths),
# follow block-based download redirects only when no credential would leave the origin, redact
# secrets from request-body debug output and error text, from command/configuration errors, and
# from the added publisher's upload redirect, token error and debug line.
set -euo pipefail
cd /app
SOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git apply --verbose "${SOL_DIR}/fix.patch" || patch -p1 < "${SOL_DIR}/fix.patch"
