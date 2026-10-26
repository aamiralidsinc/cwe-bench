#!/usr/bin/env bash
# Reference solution: vet an object-supplied Vault address against the operator's own
# configuration before it becomes the webhook's Vault address (and before any credential is
# minted), and let an object-supplied certificate-verification setting take effect only up to
# what the operator already allows.
set -euo pipefail
cd /workspace
patch -p1 --batch --forward --no-backup-if-mismatch < /solution/fix.patch
