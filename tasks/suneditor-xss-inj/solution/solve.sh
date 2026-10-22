#!/bin/bash
# Apply the reference fix to /app.
set -euo pipefail
cd /app
patch -p1 < "$(dirname "$0")/fix.patch"
