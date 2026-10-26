#!/bin/bash
# Reference fix: no route may leave a fixed administrator credential in effect. The loader stops
# inventing one, generated/example configurations stop carrying one, the credential-repair command
# refuses instead of substituting one, and startup generates and shows a fresh password when the
# operator supplied none. An explicitly supplied credential is preserved, including through a
# configuration write-out and re-read.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
