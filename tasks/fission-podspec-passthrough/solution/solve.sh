#!/bin/bash
# Apply the reference fix to the vulnerable checkout in /app.
set -euo pipefail
cd /app
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
