#!/bin/bash
# Reference fix: remove credential-bearing endpoint material from every diagnostic record the
# SDK and its exporters emit (trace/metric/log components, wrappers, caller-supplied exporters and
# clients, accepted and rejected configuration, creation/lifecycle/export records), while keeping
# each record, the component kind, non-secret settings and the export target unchanged.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
