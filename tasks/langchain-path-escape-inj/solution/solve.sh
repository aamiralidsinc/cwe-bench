#!/bin/bash
# Reference fix: confine every agent-supplied pattern/path/filename across the
# file-search tools and the file-tool commands to the configured workspace (and,
# where set, the allowed directory) — resolving symlinks and comparing on path
# segments rather than raw string prefixes — on every operation, not just the
# first observed one.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
