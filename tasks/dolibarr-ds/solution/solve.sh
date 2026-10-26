#!/bin/bash
# Reference solution: apply the record-level hierarchy checks to every employee-record route
# of the REST API, including list results, batch and derived views, and the ownership and
# approver fields accepted on creation and update.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
