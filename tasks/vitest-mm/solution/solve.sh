#!/bin/bash
# Reference solution: apply the fix to the checked-out (pinned + task) repo.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
