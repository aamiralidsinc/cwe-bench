#!/bin/bash
# Native runner for the hidden groups, run as the unprivileged agent from the
# materialized workspace. Writes JUnit XML to the path given by the caller.
set -u
mode=${1:?usage: run_n8n.sh security|functional|project <junit.xml>}
out=${2:?usage: run_n8n.sh security|functional|project <junit.xml>}

cd /workspace/packages/nodes-base || exit 1
VT=./node_modules/.bin/vitest

case "$mode" in
  security)
    $VT run test/__hidden__/security --reporter=junit --outputFile="$out"
    ;;
  functional)
    $VT run test/__hidden__/functional --reporter=junit --outputFile="$out"
    ;;
  project)
    $VT run \
      nodes/EmailSend/test/v1/EmailSendV1.node.test.ts \
      nodes/EmailSend/test/v2/send.operation.test.ts \
      nodes/EmailSend/test/v2/sendAndWait.operation.test.ts \
      --reporter=junit --outputFile="$out"
    ;;
  *)
    echo "unknown group: $mode" >&2
    exit 2
    ;;
esac
