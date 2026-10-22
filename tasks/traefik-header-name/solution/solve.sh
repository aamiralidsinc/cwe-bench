#!/bin/bash
# Reference fix: the published entry-point option for headers with underscores,
# plus removal of every spelling of a header that a middleware sets or strips.
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
