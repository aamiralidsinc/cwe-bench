#!/bin/bash
# Reference fix: default Display/Debug diagnostics of errors and result values
# omit server-provided and caller-secret content, while explicit fields and
# accessors keep returning the original values.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
