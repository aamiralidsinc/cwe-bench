#!/bin/bash
# Reference fix: remove the three launcher types from the shared extension allowlist while letting
# the product's own shortcut writer keep them, and make every naming route that builds a final
# suffix from a download's own file type validate it first.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
