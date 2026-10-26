#!/bin/bash
# Reference fix: clamp every path the product resolves on behalf of archive, image and
# backup content so each hop stays inside the container, and re-resolve paths after
# unpacking wherever they are acted on later.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
