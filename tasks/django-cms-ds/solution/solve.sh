#!/bin/bash
# Reference fix: the published source changes for the page-creation authorization flaw,
# the site-aware view decision, the real routes the published fix left open, the
# task's page-administration additions, and the placement/home-page routes.
set -euo pipefail
cd /workspace
patch -p1 --forward < /solution/fix.patch
