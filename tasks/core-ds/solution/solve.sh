#!/bin/bash
# Reference fix: contain every path derived from an uploaded archive's metadata and from a
# backup creation name, on every operation that writes one.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
