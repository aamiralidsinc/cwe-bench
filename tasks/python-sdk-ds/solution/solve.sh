#!/bin/bash
# Reference fix: give every task an owner decided when the task is created, and decide
# every task operation (status, payload, listing, cancellation, removal, subscription)
# against that owner. Tasks created without a session association stay usable by their
# exact identifier and are never enumerated.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
