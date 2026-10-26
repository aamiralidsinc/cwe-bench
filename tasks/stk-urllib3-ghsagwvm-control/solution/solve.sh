#!/bin/bash
# Reference fix: withhold the caller's credential headers from every request that a redirect
# moves to a different origin, in each redirect-following path the package offers, while
# same-origin redirects and non-redirect requests keep every header.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
