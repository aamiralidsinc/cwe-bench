#!/bin/bash
# Reference fix: make the shared option-candidate builder see every token a caller's option will
# become, add the missing command alias to the remote-listing blocklist, and screen the diff path.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
