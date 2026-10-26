#!/bin/bash
# Reference fix: decide namespace scope on whole labels in every store backend, every read and
# listing path, every connection setup and every namespace-scoped bulk helper.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
