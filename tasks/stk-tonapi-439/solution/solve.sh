#!/bin/bash
# Reference fix: provision one TONAPI webhook and one secret for every registered
# delivery route, route every registered route to its event kind, clean up exactly
# the webhooks provisioning created, and refuse a delivery to a route for which no
# secret was issued while the dispatcher is bound to a TONAPI client.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
