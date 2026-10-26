#!/bin/bash
# Reference fix: enforce each Feishu account's effective tool setting at execution (documents,
# the app-scope diagnostic with its own setting, wiki, drive, permissions), select an allowed
# account when a request names none, and gate the two hand-rolled account selections (chat and
# the bulk Bitable import) through the same resolver.
set -euo pipefail
cd /workspace
if [ -f /solution/fix.patch ]; then
  patch -p1 < /solution/fix.patch
else
  patch -p1 < "$(dirname "$0")/fix.patch"
fi
