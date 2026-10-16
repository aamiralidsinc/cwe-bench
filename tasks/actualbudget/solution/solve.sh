#!/bin/bash
# Reference solution: apply the upstream security fixes to /app.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
echo "Applied reference fix."
