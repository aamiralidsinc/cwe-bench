#!/bin/bash
# Fetch the code for each screening host: pinned tree, published fix diff, current upstream tree.
# Usage: fetch_hosts.sh ROOT [LIST]   (LIST, default ROOT/hosts.tsv: entry_id repo fix_commit parent_commit advisory)
# Writes ROOT/hosts/<entry_id>/{repo/,fix.diff,latest/,latest.txt,pinned.txt}. No .git is kept, so
# a screener sees the pinned state only. Network: github.com (git) only.
set -euo pipefail
ROOT=$1
while IFS=$'\t' read -r eid repo fix parent adv; do
  # read merges empty tab-separated fields: anything that is not a commit hash means "no parent"
  [[ $parent =~ ^[0-9a-f]{7,40}$ ]] || parent=""
  H=$ROOT/hosts/$eid; mkdir -p "$H"; G=$ROOT/git/$eid
  if [ -s "$H/fix.diff" ] && [ -d "$H/repo" ] && [ -d "$H/latest" ]; then echo "$eid: done"; continue; fi
  rm -rf "$G" "$H/repo" "$H/latest"; git init -q "$G"
  git -C "$G" remote add origin "https://github.com/$repo.git"
  git -C "$G" fetch -q --depth 2 origin "$fix"
  [ -n "$parent" ] || parent=$(git -C "$G" rev-parse "$fix^1")
  git -C "$G" cat-file -e "$parent^{commit}" 2>/dev/null || git -C "$G" fetch -q --depth 1 origin "$parent"
  git -C "$G" diff "$parent" "$fix" > "$H/fix.diff"
  mkdir -p "$H/repo"; git -C "$G" archive "$parent" | tar -x -C "$H/repo"
  echo "$parent" > "$H/pinned.txt"
  # current upstream code = default branch HEAD (GitHub "latest release" picks monorepo sub-packages
  # or legacy lines, e.g. hono -> @hono/vercel, pyload -> v0.4.x)
  git -C "$G" fetch -q --depth 1 origin HEAD
  mkdir -p "$H/latest"; git -C "$G" archive FETCH_HEAD | tar -x -C "$H/latest"
  echo "current upstream: default branch HEAD $(git -C "$G" rev-parse FETCH_HEAD) ($(date -u +%F))" > "$H/latest.txt"
  rm -rf "$G"
  echo "$eid $repo pinned=${parent:0:10} fix=${fix:0:10} $(cat "$H/latest.txt") diff=$(wc -l < "$H/fix.diff") lines"
done < "${2:-$ROOT/hosts.tsv}"
