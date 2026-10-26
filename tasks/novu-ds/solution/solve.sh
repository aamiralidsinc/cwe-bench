#!/bin/bash
# Apply the reference fix to the restored submission.
set -euo pipefail
cd /workspace
patch -p1 < "$(dirname "$0")/fix.patch"
