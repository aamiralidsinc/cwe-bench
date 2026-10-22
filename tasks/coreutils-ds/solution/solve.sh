#!/bin/bash
# Reference fix: every route that creates a destination directory or places the destination file
# anchors its work on a directory file descriptor and refuses a symbolic link in the components it
# has to create or write through; the destination-directory write path refuses a link standing for
# the directory itself; the loop/re-install write path replaces a link at the destination name
# instead of following it; and the backup rename no longer resolves the destination first. Existing
# symlinked prefixes and all ordinary install behaviour are preserved.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
