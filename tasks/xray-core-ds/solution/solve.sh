#!/bin/bash
# Reference fix: bind every pinned-CA client handshake to the host it connects to (and refuse a
# pinned-CA handshake when no host is known), while pinned-leaf connections, configured server
# names and correctly named pinned-CA connections keep working.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
