#!/bin/bash
# Reference fix: resolve every injected path as the privileged writer that will
# use it, and refuse any path that leaves the mounted image.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
