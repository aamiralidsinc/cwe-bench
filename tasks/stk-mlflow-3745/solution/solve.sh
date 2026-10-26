#!/bin/bash
# Reference fix: refuse a supplied or stored configuration whose destination is not
# publicly routable, wherever the destination is determined, while keeping the
# shipped provider defaults and legitimate public configuration working.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
