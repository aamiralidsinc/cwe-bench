#!/bin/bash
# Apply the reference fix to the checked-out (pinned + task) repository.
set -euo pipefail
cd /app
patch -p1 < "$(dirname "$0")/fix.patch"
