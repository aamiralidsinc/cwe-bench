#!/bin/bash
# Reference fix: bound the work a broker-chosen authentication challenge may demand (both the
# iteration count and the salt that multiplies it), bound the output of every decompression
# decoder while still streaming, and require a compressed legacy message set to make progress
# on each declared message length.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
