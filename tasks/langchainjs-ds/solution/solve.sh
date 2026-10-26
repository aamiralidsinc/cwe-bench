#!/bin/bash
# Reference fix: the published RediSearch query-hardening source change, extended to
# cover the value kinds the published fix left interpolated, the field names of every
# filter kind, and the sibling filter paths this image adds.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
