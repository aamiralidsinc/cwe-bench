#!/bin/bash
# Reference fix: emit every supplied value as escaped data (Solidity and TypeScript literals),
# refuse values that cannot stay inside a single-line comment, and use the Solidity serializer
# at the places that hand-rolled a JavaScript one.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
