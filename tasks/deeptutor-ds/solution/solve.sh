#!/bin/bash
# Reference fix: resolve MCP-tool access per turn and apply it wherever a deferred
# tool can be listed, loaded or run.
set -euo pipefail
cd /workspace
patch -p1 < "$(dirname "$0")/fix.patch"
