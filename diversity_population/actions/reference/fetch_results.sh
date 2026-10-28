#!/bin/bash
# Download and decrypt the matrix run's artifacts into actions/results/<id>/ (never into root/ directly).
#   KEY_FILE=... REPO=<owner>/<repo> bash fetch_results.sh <run-id>
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RUN=${1:?usage: fetch_results.sh <run-id>}; KEY_FILE=${KEY_FILE:?}; REPO=${REPO:?}
DL=$(mktemp -d); trap 'rm -rf "$DL"' EXIT
gh run download "$RUN" -R "$REPO" -D "$DL"
for f in "$DL"/*/*.tgz.gpg; do
  id=$(basename "$f" .tgz.gpg); out="$HERE/results/$id"; mkdir -p "$out"
  gpg --batch --quiet --pinentry-mode loopback --passphrase-file "$KEY_FILE" -d "$f" | tar -xz -C "$out"
  m=none; for x in .sound .unsound .gate_error; do ls "$out"/root/build/*/"$x" >/dev/null 2>&1 && m=$x; done
  echo "$id -> $(jq -r --arg i "$id" '.[$i]' "$HERE/ids.local.json"): $m"
done
