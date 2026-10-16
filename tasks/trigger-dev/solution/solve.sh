#!/bin/bash
set -euo pipefail
cd /app
git apply -p1 /solution/fix.patch || patch -p1 --no-backup-if-mismatch < /solution/fix.patch
