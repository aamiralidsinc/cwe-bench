#!/bin/bash
# Reference fix: make adjacent text merging, attribute-block accumulation, per-target attribute
# merging and attribute target resolution all cost work proportional to what each input adds.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
