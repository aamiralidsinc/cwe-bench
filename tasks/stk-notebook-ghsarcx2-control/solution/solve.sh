#!/bin/bash
# Reference fix: decide every redirect destination on the form a browser resolves, reject a
# request target that would be read as an authority, and rebase a configured landing address
# that carries a scheme or authority below the server prefix.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
