#!/bin/bash
# Reference fix: confine include targets to the include base at the parsing layer every entry
# point uses, apply the same confinement in the separate dependency resolver, and keep resolved
# filesystem locations out of generated comments and formatted diagnostics.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
