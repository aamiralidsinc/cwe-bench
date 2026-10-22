#!/bin/bash
# Reference solution: apply the reference source fix to the checked-out
# (pinned + task) repository.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
