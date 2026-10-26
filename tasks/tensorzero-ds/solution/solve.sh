#!/bin/bash
# Reference fix: every untrusted read of a stored object goes through a key-only
# fetch that always uses the gateway's configured object store.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
