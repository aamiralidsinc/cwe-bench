#!/usr/bin/env bash
# Reference solution: refuse dangerous LESS features in every stored value that is spliced
# into the stylesheet source (the custom-LESS setting, settings registered as LESS config
# variables, and extension-declared LESS variables).
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
