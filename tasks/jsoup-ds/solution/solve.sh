#!/bin/bash
# Reference fix: reconcile the tag name the tokeniser records with the name the tag registry
# resolves (stop trimming control characters out of token names; trust a supplied normal name in
# the registry, keeping documented trimming for public-API lookups), and remove the two
# tree-builder sites that re-normalise a start tag's name before the tag lookup / text-state
# decision. Allowed opaque elements keep their content; public tag lookups still trim.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
