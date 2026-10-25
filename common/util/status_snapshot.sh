#!/bin/bash
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
cd "$CWE_ROOT" || exit 1
echo "===== CWE-bench status $(date -u +%H:%M:%SZ) ====="
echo "procs: trial.py=$(pgrep -fc common/trial/trial.py) harbor=$(pgrep -fc harbor) fairfix=$(pgrep -fc run_fairfix.sh) gate=$(pgrep -fc common/gate/gate.py) containers=$(docker ps -q|wc -l) load=$(uptime|grep -oE 'load average.*')"
echo "--- TRIALS (runs/last-reward per model; trailing R = still running) ---"
for s in whistle-cwe-path flyto-core-path-traversal compliance-trestle-path-traversal traefik-header-name django-cms-object-level fission-podspec-passthrough docling-file-disclosure astro-csrf-origin electron-builder-credential-leakage seaweedfs-s3tables-authz vibe-trading-path-read nhost-cors-auth; do
  line="$s"
  for m in deepseek mimo; do
    l=build/$s/runs_$m.log
    if [ -f "$l" ]; then n=$(grep -c reward= "$l"); last=$(tail -1 "$l" | grep -oE 'reward=[^ 	]+' | cut -d= -f2); run=$([ "$(pgrep -fc "trial.py $s --models $m")" -gt 0 ]&&echo R||echo .); line="$line  $m:${n}/${last}$run"; else line="$line  $m:-"; fi
  done
  echo "  $line"
done
