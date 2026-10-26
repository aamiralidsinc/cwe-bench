#!/bin/bash
# Reference fix: redact configured credentials (key names, login names and URL
# userinfo) in every unauthenticated read-only view, including values that are
# stored in lists or nested structures.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
