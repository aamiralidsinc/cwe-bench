#!/bin/bash
# Reference fix: confine every asset operation's writes to the temporary location it creates,
# while keeping legitimate nested attachments, identifiers and imports unchanged.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
