#!/bin/bash
# Reference fix: confine every author-controlled file reference the prompt
# runtimes follow (frontmatter references, inherited documents, template
# snippets, and the companion-prompt path of a prompt-kind tool) to the prompt's
# own directory, in each language package this repository ships.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
