#!/usr/bin/env bash
# Reference solution: reject reserved and IPv6-transition-embedded addresses wherever the product
# opens a connection on behalf of a URL, and classify them at the shared dial guard, while keeping
# the local/private and file-based endpoints the product supports today.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
