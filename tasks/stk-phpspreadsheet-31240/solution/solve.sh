#!/usr/bin/env bash
# Reference solution: bound the decoded size of a compressed workbook, add a per-chain visited-block
# guard to every sector-chain walk in both container implementations, and bound the archive entries
# the zip-based readers inflate.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
