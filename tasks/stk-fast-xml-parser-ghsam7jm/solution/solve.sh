#!/usr/bin/env bash
# Reference solution: consume entity names literally wherever a reference matcher is built from
# a name, and insert declared replacement text literally.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
