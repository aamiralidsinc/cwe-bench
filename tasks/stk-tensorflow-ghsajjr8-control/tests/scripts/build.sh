#!/bin/bash
# Rebuild the runtime library from the restored tree. Run as the unprivileged
# user, offline. Unchanged objects are reused.
set -u
B=/opt/tflite-build
# A restored file whose timestamp is older than the object built from it would
# be skipped by the build system; touch the files whose content changed.
if [ -f /opt/pristine.sha256 ]; then
  while read -r sum path; do
    [ -f "$path" ] || continue
    cur=$(sha256sum "$path" | cut -d' ' -f1)
    [ "$cur" = "$sum" ] || touch "$path"
  done < /opt/pristine.sha256
fi
export PATH=/usr/local/bin:/usr/bin:/bin
exec ninja -C "$B" -j8 tensorflowlite
