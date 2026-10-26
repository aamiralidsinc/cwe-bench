#!/bin/bash
# Reference fix: a storage destination (root and relative path) supplied by a client is only
# accepted when it stays inside the storage areas the server manages, every write path applies
# that containment before creating anything, and a plugin may only be selected by an installed
# package name (imports and deletions alike). Operator-seeded storage roots keep working.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
