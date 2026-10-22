#!/bin/bash
# Reference fix: the published table-storage authorization fix, plus the two
# routes it left open (identity-provider claims and client account headers).
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
