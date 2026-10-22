#!/bin/bash
# Reference fix: before a package's declared binary is chmod'd or proxied, require
# that it resolves (symlinks included) to a path inside the package's own install
# directory, on every install/download/refresh path that touches it. Fail closed if
# a path cannot be resolved; legitimate in-package bins and symlink installs are kept.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
