#!/bin/bash
# Reference fix: scope every MCP surface and every stored-file operation to the
# caller and the addressed namespace, in both storage implementations.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
