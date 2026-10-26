#!/bin/bash
# Reference fix: apply the exact-identity comparison to every lookup that maps an external
# subject to a local account (both protocols, both orphan cleanups, both link writes), and make
# the shipped identity columns/unique indexes byte-exact for installations created from the
# schema file.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
