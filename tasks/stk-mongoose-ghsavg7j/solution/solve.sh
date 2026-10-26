#!/bin/bash
# Reference solution: apply the complete published fix for the reported incomplete repair
# (recursively refusing the script operator at every populate-match site) plus the guards for
# the other routes that can still carry caller-supplied server-side JavaScript to the database.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
