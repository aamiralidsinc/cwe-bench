#!/usr/bin/env bash
# Reference fix: sanitize every destination the product stores or returns before it can reach
# the browser, and refuse or replace script-capable values at the points where a request supplies
# one. The shared check removes markup and template-tag braces before inspecting the scheme,
# because the product's own handling removes them before the browser follows the value.
set -euo pipefail

cd /workspace
patch -p1 --batch --forward < /solution/fix.patch
