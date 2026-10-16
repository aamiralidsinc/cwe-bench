#!/bin/bash
# Reference solution: apply the reference source fix to the checked-out repo.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
