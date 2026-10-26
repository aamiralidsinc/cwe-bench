#!/bin/bash
# Reference fix: a folder capability is only handed out to a caller who already has
# that folder's access, share nodes cannot carry a folder capability for a source
# folder they do not expose, and a folder key that does not include subfolders cannot
# reach them through an archive selection.  Ordinary browsing, file-key links and
# folder shares keep working.
set -euo pipefail
cd /workspace
patch -p1 --forward --no-backup-if-mismatch < /solution/fix.patch
