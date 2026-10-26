#!/bin/bash
# Reference fix for the control task: the published fix, reduced to source changes.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
