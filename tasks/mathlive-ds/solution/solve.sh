#!/usr/bin/env bash
# Reference fix: the published output-encoding change, extended to every producer that
# emits element content (HTML renderer, MathML serializer and its delimiter sites, the
# speakable output and the static renderer sink) and to the sibling paths this image adds.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
