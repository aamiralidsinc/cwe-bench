#!/bin/bash
# Reference solution: apply the complete fix to the checked-out (pinned) repository.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
