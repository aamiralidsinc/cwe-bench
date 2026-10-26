#!/bin/bash
# Reference solution: apply the model class-name filter to every class reference a model can feed
# to a reflective load, and close the adapter and model-element routes the reported path misses.
set -euo pipefail
cd /workspace
patch -p1 < /solution/fix.patch
