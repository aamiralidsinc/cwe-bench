#!/bin/bash
# Reference fix: keep every name that becomes a path inside the workspace the command
# runs in, and decide that before anything is created, replaced or deleted.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
