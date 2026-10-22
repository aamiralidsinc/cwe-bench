#!/bin/bash
# Applies the oracle fix to /app. Used by the gate's oracle stage.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
echo "oracle fix applied"
