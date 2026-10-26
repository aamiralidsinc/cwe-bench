#!/usr/bin/env bash
# Reference solution: strip behavior and event configuration keys from the posted field layout
# settings helper and the layout save service, apply the same recursive cleanser in the field
# layout/tab factories and to element duplication attributes, and make duplication accept only
# already-instantiated behaviors.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
