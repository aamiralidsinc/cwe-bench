#!/usr/bin/env bash
# Reference solution (control): consume document-declared entity names literally when the
# matcher for their references is built.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
