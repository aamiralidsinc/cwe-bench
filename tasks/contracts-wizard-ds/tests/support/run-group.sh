#!/usr/bin/env bash
# Run one hidden group with the project's native TypeScript loader (ts-node, transpile-only, the
# same way the project's own ava setup loads its sources) and write JUnit XML to $2.
set -u
group="$1"
out="$2"
cd /workspace

export PRODUCT_ROOT=/workspace
export NODE_OPTIONS="--require /workspace/node_modules/ts-node/register/transpile-only"
export TS_NODE_PROJECT=/workspace/packages/core/solidity/tsconfig.json
export TS_NODE_TRANSPILE_ONLY=1

node --test --test-reporter=junit --test-reporter-destination="$out" /workspace/.htests/"$group"/*.test.cjs
