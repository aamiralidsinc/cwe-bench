#!/bin/bash
# Reference solution: the upstream fix for Docling JSON input plus the same
# local-image filtering on the routes it did not cover (saved conversion
# archives, documents returned by a conversion service).
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
