#!/bin/bash
set -euo pipefail
# Apply the reference fix to the project in /workspace.
DIR=$(cd "$(dirname "$0")" && pwd)
patch -p1 -d /workspace < "$DIR/fix.patch"
