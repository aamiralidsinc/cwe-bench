#!/usr/bin/env bash
# Apply the reference fix to the project tree.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
