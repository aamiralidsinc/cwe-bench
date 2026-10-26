#!/bin/bash
# Reference fix: resolve every stored content type through one safe allowlist before any Blob or
# URL is built, and route every generated client action (including the second preview actions)
# through it.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
