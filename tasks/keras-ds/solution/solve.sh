#!/bin/bash
# Reference fix: reject links, external storage and virtual datasets wherever a
# model or weights HDF5 file is read — the core store (single, archive, sharded
# and top-level container), the older single-file loader including its optimizer
# state, the dispatch layer's container lookup, and the weights-file inspection
# utility — while keeping ordinary files loading.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
