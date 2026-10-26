#!/bin/bash
# Reference fix: never put an exception's own text into the status a client can
# see; the detail text is a fixed generic message unless the operator explicitly
# turns detailed diagnostics back on.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
