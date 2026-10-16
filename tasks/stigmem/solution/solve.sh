#!/bin/bash
# Reference solution: apply the upstream source fixes for all co-present flaws.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
