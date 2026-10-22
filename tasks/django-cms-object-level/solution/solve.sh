#!/bin/bash
# Reference fix: the published source changes plus the same view check on the
# page-type source shared by the add form and the page wizard, evaluated on the
# source's own site (page-type choices narrowed to this site, and the view
# helper's change shortcut made site-aware).
set -euo pipefail
cd /app
patch -p1 --forward < /solution/fix.patch
