#!/bin/bash
# Reference fix: the published table-storage authorization fix, plus every
# route it left open (identity-provider claims, client account headers, bare
# admin names, catalog create-before-authorize) and the task-local operations.
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
