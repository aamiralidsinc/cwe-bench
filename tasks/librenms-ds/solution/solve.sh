#!/bin/bash
# Reference fix: keep every device-supplied value inert wherever a server-rendered page, partial
# or hover tooltip displays it, including values recorded earlier with an alert.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
cd /workspace
patch -p1 < "$here/fix.patch"
