#!/usr/bin/env bash
# Reference solution (control): strip behavior and event configuration keys, recursively, from
# the document the field layout save service decodes before it builds the layout.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
