#!/bin/bash
# Reference solution for the control task: the published fix for the reported fetch, applied to the
# checked-out pinned repository.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
