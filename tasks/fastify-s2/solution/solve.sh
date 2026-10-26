#!/bin/bash
# Reference fix: the published change plus the other places that decide whether a
# request schema is present -- the documented request-part alias, the not-found
# handler context, the server-wide default merge and the inline request validation
# helper.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
