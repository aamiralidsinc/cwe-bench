#!/bin/bash
# Robust per-artifact fetch for a flaky/slow link: enumerate all artifacts across the given
# <repo>:<run> pairs, fetch SMALLEST first, each with retries, decrypt immediately into results/<name>,
# delete the zip. A connection reset loses only one artifact's attempt, retried — not the whole run.
#   KEY_FILE=... bash robust_fetch.sh results aamiralidsinc/build-matrix-k7:39870845060 ...
set -uo pipefail
OUT=$1; shift
KEY_FILE=${KEY_FILE:?}; HERE=$(cd "$(dirname "$0")" && pwd); DEST="$HERE/$OUT"; mkdir -p "$DEST"
log(){ echo "$(date -u +%H:%M:%S) $*"; }
# Build "size name repo run" list across all pairs
list=$(for p in "$@"; do R=${p%:*}; run=${p##*:}
  gh api "repos/$R/actions/runs/$run/artifacts" --paginate -q ".artifacts[]|\"\(.size_in_bytes) \(.name) $R $run\"" 2>/dev/null
done | sort -n)
total=$(echo "$list" | grep -c .); log "robust_fetch: $total artifacts queued (smallest first) -> $DEST"
echo "$list" | while read size name R run; do
  [ -z "$name" ] && continue
  [ -d "$DEST/$name/root" ] && { log "skip $name (already have)"; continue; }
  mb=$((size/1048576)); ok=0
  for a in 1 2 3 4 5; do
    tmp=$(mktemp -d)
    if gh run download "$run" -R "$R" -n "$name" -D "$tmp" >/dev/null 2>&1; then
      f=$(find "$tmp" -name '*.tgz.gpg' | head -1)
      if [ -n "$f" ] && gpg --batch --quiet --pinentry-mode loopback --passphrase-file "$KEY_FILE" -d "$f" 2>/dev/null | tar -xz -C "$(mkdir -p "$DEST/$name"; echo "$DEST/$name")" 2>/dev/null; then
        ok=1; rm -rf "$tmp"; break
      fi
    fi
    rm -rf "$tmp"; log "  $name (${mb}MB) attempt $a failed; retry"; sleep $((a*15))
  done
  m=none; for x in .sound .unsound .gate_error; do ls "$DEST/$name"/root/build/*/"$x" >/dev/null 2>&1 && m=$x; done
  [ "$ok" = 1 ] && log "got $name (${mb}MB) marker=$m" || log "GAVE UP on $name (${mb}MB) after 5 tries"
done
log "robust_fetch DONE -> $DEST ($(ls "$DEST" | wc -l | tr -d ' ') dirs)"
