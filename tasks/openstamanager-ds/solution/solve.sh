#!/bin/bash
# Reference solution: treat every stored value as text at the layer that produces each surface
# of the product (record pages, search suggestions, and the link helpers both of them use).
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
