#!/bin/bash
# Build the encrypted payload for the Actions build matrix: arm A only (21 tasks), opaque ids t01..t21
# in pre-registered build order. Nothing readable leaves this machine: the repo gets payload.tar.gz.gpg.
#   KEY_FILE=~/.tb-graders/cwe/precision_validation/payload.key bash make_payload.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); PV=$(dirname "$HERE")
KEY_FILE=${KEY_FILE:?set KEY_FILE to the passphrase file (create: openssl rand -base64 48 > FILE; chmod 600 FILE)}
STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"' EXIT
python3 - "$PV" "$STAGE" <<'EOF'
import csv, json, shutil, sys, os
pv, st = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(f'{pv}/results/build_slugs.csv')) if r['arm'] == 'A']
rows.sort(key=lambda r: int(r['build_order']))
ids = {f't{i:02d}': r['slug'] for i, r in enumerate(rows, 1)}
json.dump(ids, open(f'{st}/ids.json', 'w'), indent=1)
skip = {d for d in os.listdir(f'{pv}/root/build') if d.startswith('pv-') and d not in ids.values()}
shutil.copytree(f'{pv}/root', f'{st}/root', ignore=lambda d, names: [n for n in names if n in skip])
print(f'{len(ids)} arm-A tasks staged; {len(skip)} other build dirs left out')
EOF
cp "$STAGE/ids.json" "$HERE/ids.local.json"     # local copy of the id -> slug map (never pushed)
# The project root named in the build prompts; the workflow reads it from here so it never appears in plain text.
python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['project_root'].rsplit('/root',1)[0])" \
  "$(ls "$STAGE"/root/build/pv-*/spec.json | head -1)" > "$STAGE/pv_path"
tar -czf "$STAGE/payload.tar.gz" -C "$STAGE" root ids.json pv_path
gpg --batch --yes --pinentry-mode loopback --passphrase-file "$KEY_FILE" --symmetric --cipher-algo AES256 \
    -o "$HERE/repo/payload.tar.gz.gpg" "$STAGE/payload.tar.gz"
ls -la "$HERE/repo/payload.tar.gz.gpg"
