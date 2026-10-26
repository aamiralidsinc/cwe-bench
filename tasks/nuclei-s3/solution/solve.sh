#!/bin/bash
# Reference fix: render template-authored text once and treat every value that
# came from the scan target as terminal data on every evaluation path.
set -euo pipefail
cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
