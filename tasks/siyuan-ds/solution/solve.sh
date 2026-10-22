#!/bin/bash
# Reference fix: apply the publish access rules to the static resource routes,
# the preview routes, and the metadata APIs.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
