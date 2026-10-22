#!/bin/bash
# Reference solution: validate every identifier-like value carried by a class
# definition, quote every definition-derived identifier used in DDL, and keep
# free text inert when it is written into generated code.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
