#!/bin/bash
# Reference fix: the deployment-wide model/vector configuration is operator-owned, the read
# response discloses no part of a stored credential and works when none is configured, and
# anonymous account creation is closed on deployments that require authentication unless the
# operator opens it.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
