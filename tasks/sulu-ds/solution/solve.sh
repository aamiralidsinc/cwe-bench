#!/usr/bin/env bash
# Reference fix: require VIEW on the security context of the content behind a preview link before
# the link is minted, rotated or revoked or an existing link is returned, and put the check in the
# application service so every caller of the service inherits it.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
