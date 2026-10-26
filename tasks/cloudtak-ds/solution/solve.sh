#!/bin/bash
# Reference fix: classify the stored ESRI-layer destination before the ESRI client is used,
# narrow the tile-origin exemption to the origin the operator configured, re-validate every
# redirect hop through the guarded fetch client, and classify the destinations reached by the
# warm-up helper and the advertised-tile probe while keeping the configured origin allowed.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
