#!/bin/bash
# Reference fix: one shared threat-pattern library used by every context-file,
# memory and tool-result path; load-time snapshot sanitisation; provider-block
# and recalled-context sanitisation; untrusted-data framing for third-party
# tool results (including the alternate transport and the optional search
# tool); and the two additional write/discovery paths in our copy.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
