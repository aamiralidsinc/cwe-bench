#!/bin/bash
# Reference solution: gate every control-panel navigation read on the view right for the
# navigation in the site being read and on the view right for the entry each page links to,
# and stop the navigation tree serializer from emitting entry-derived values the caller may
# not view (including in the response to saving the tree).
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
