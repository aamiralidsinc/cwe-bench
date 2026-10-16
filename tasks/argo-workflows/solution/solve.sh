#!/bin/bash
# Reference solution: apply the upstream source fixes to /app.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
