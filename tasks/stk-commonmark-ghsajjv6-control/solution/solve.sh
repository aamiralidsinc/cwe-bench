#!/bin/bash
# Reference fix for the reported path: append into the surviving text node instead of copying the
# whole accumulated literal on every merge.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
