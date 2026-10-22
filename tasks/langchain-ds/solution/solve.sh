#!/bin/bash
# Reference fix: confine every agent-supplied pattern, path and command argument
# across the file-search tools and the file-tool commands to the configured
# workspace (and, where set, the allowed directory) — resolving symlinks and
# comparing on whole path segments — on every operation the components offer.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
