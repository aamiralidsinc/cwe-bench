#!/usr/bin/env bash
# Prepare the restored workspace for the hidden suites, as the unprivileged test user.
# The artifact excludes dependency trees, so the verifier's pristine tree is linked in, and the
# two generated assets the project's build normally writes are recreated (the generators read
# one of them for the OpenZeppelin Contracts version).
set -eu
cd /workspace

if [ ! -e node_modules ] || [ ! -e node_modules/ts-node ]; then
  rm -rf node_modules
  ln -s /opt/wizdeps/node_modules node_modules
fi

node -e 'const fs = require("fs"); const v = "5.6.0"; fs.writeFileSync("packages/core/solidity/openzeppelin-contracts.json", JSON.stringify({ version: v, sources: {}, dependencies: {} }, null, 2)); fs.writeFileSync("packages/core/solidity/openzeppelin-contracts-version.json", JSON.stringify({ version: v }, null, 2));'
