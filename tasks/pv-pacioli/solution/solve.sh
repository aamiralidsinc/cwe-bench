#!/usr/bin/env bash
# Apply the reference fix to the restored workspace.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patch -p1 -d /workspace --batch --forward --no-backup-if-mismatch < "$here/fix.patch"
echo "reference fix applied to /workspace"
