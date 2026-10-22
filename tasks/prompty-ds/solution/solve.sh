#!/bin/bash
# Reference fix: confine every author-controlled reference in a prompt document
# (frontmatter protocols, composition features and child-prompt tool paths) to
# the directory that contains the document, in every runtime the project ships
# that this task exercises.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
