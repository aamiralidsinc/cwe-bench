#!/bin/bash
# Apply the reference fix to the restored workspace.
set -euo pipefail
cd /workspace
patch -p1 --forward --batch < /solution/fix.patch
