#!/bin/bash
set -euo pipefail
# Apply the reference fix to the checked-out repository.
cd /app
patch -p1 < /solution/fix.patch
