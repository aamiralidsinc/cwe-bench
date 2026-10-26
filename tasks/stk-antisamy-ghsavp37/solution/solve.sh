#!/bin/bash
# Reference fix. Style content is validated as one stylesheet before a single cleaned child is
# serialised; an on-site reference cannot become a reference to another origin once a browser has
# normalised it; and only elements the HTML grammar defines as empty are serialised self-closed,
# so every container element carries an explicit closing tag.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
