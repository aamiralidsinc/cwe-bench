#!/bin/bash
# Reference fix: apply the publication-window visibility predicate to every public FAQ reader,
# give the public feed a public-only query mode, and derive the preview's privileged branch from
# the caller's actual editing permission.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
