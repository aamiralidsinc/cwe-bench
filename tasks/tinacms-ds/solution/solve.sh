#!/bin/bash
# Reference fix: resolve every caller-supplied media key and directory against
# the operator's media root on every adapter and every route (presigned upload,
# direct upload, delete, batch delete, copy/move, listing), refusing absolute,
# traversal, NUL/backslash and empty values with a client error.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
