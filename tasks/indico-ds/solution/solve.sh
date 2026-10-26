#!/bin/bash
# Reference fix: restrict every user-supplied link target to ordinary web addresses and
# sanitize stored minutes HTML on every delivery path, keeping the raw authored text intact.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
