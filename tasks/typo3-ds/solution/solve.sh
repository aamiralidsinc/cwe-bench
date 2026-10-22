#!/bin/bash
# Reference solution: apply the source fix (published fix plus the added
# persistence paths) to the checked-out project.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
