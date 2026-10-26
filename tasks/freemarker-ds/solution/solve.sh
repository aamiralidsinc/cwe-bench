#!/bin/bash
# Reference fix: the localized lookup rebuilds the locale infix from the locale parts, cutting each
# part at the first path separator, percent sign or control character; the class-loader root guard
# no longer depends on the stored base path; the alternate locale-directory convention applies the
# same part sanitisation; and a condition-derived override directory must stay inside the root.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
