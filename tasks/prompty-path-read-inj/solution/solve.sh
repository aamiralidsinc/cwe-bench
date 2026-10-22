#!/bin/bash
# Reference fix: confine every author-controlled file reference in the prompt
# loader (the frontmatter reference protocols, the base-template include, and
# the child-prompt path of a prompt-kind tool) to the prompt's own directory.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
