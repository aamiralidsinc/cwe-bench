#!/bin/bash
# Reference fix: contain every identifier-to-filename mapping in the document,
# memory and template stores (reads, writes, rename, delete, imported-doc
# lookup, previews and recovery views), rejecting traversal, absolute/volume
# spellings and symlink escapes, and validating memory identifiers — including
# identifiers read back from a stored record.
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
