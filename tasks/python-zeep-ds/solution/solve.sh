#!/bin/bash
# Reference fix: block every transitive remote document reference when the
# external-reference protection is enabled, while the entry document the
# application supplied still loads and the default configuration is unchanged.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
