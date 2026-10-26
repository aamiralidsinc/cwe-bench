#!/bin/bash
# Reference fix: close the reported download route and the sibling serving route.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
