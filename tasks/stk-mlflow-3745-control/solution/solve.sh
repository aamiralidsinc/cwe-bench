#!/bin/bash
# Reference fix for the control task: refuse a supplied configuration whose destination
# is not publicly routable when a gateway secret is created or updated.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
