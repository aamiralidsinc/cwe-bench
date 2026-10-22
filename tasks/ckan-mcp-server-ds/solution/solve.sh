#!/bin/bash
# Reference fix: the published SSRF fix (shared IP-range test, resolution at
# connection time with the validated address pinned, a redirect cap, a
# pre-resolution check on the fetch-based SPARQL path, and a mandatory permitted
# hosts list for the network transport) plus the same protection for the sibling
# fetch/probe sites this image adds.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
