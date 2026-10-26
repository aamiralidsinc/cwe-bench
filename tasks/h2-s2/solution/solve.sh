#!/bin/bash
# Reference fix: make every request-header validator count the destination fields rather than
# overwrite them, and let a request's later header block reject a repeated destination.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
