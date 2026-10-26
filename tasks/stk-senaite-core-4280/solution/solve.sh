#!/bin/bash
# Reference fix: authorize every field write against the field's own write
# permission, treat record text as data everywhere it is parsed, and let a read
# return only read-only computed values.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
