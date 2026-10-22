#!/bin/bash
# Reference fix: the published fix's source changes. The local configuration
# service grants CORS only to the local dashboard's origins (through a new
# predicate option of the shared CORS middleware), loads secrets with their
# values replaced by a placeholder, and merges placeholder values with the
# on-disk secrets when persisting secret changes. App ID wiring is included.
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
