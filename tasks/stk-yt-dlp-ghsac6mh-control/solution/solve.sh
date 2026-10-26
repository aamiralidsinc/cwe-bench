#!/bin/bash
# Reference fix: apply the extension policy to the extension-changing helpers and keep
# shortcut types to the link-writing feature.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
