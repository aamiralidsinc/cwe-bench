#!/bin/bash
# hourly_cleanup.sh: the owner-approved Docker/disk cleanup, PERMANENT and part of the pipeline (owner decision
# 2026-10-27). Removes only leftovers that nothing uses:
#   1. stopped run containers that exited more than 1 h ago
#   2. per-run images (names with __<7 chars>__) older than 1 h; Docker refuses any image still in use
#   3. gate-run folders under ~/.tb-graders/cwe/gate-jobs older than 1 h that no running gate names
#   4. unused Docker build cache (docker builder prune --all; Docker keeps cache an active build uses)
#   5. dangling images (untagged leftovers of rebuilt tags)
#   6. shared task images (cwe-reuse/<task>:<env|verifier>-<hash>, common/harbor_ext/cwe_reuse_env.py) that no
#      run, gate or regrade has used for CWE_REUSE_KEEP_H hours (default 24); Docker refuses any image in use
# Tasks under repair (build/<slug>/.hold-repair) keep their containers and images. Nothing in use is touched.
#
#   bash common/util/hourly_cleanup.sh once     # one pass now (also what the permission rule allows on demand)
#   bash common/util/hourly_cleanup.sh loop     # one pass every CLEANUP_EVERY_MIN minutes (default 60), forever
# Log: build/audit/hourly_cleanup.log. Loop PID: build/audit/hourly_cleanup.pid
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/common/paths.sh"
cd "$CWE_ROOT" || exit 1
L=build/audit/hourly_cleanup.log
log() { echo "$(date -u +%FT%TZ) $*" >> "$L"; }
freegb() { df -BG / | tail -1 | awk '{print $4}' | tr -d G; }

pass() {
  local keep n
  keep=$(ls -d build/*/.hold-repair 2>/dev/null | awk -F/ '{print $2}' | paste -sd'|' -)
  [ -z "$keep" ] && keep='^$'
  log "pass start: free $(freegb) GB; repair tasks kept: $keep"
  # 1. stopped containers exited > 1 h
  timeout 600 docker ps -a --filter status=exited --filter status=dead --format '{{.ID}}|{{.Names}}|{{.Status}}' 2>/dev/null |
    while IFS='|' read -r id name status; do
      echo "$name" | grep -qiE "$keep" && continue
      case "$status" in *"About an hour ago"*|*" hours ago"*|*" days ago"*|*"a day ago"*|*" weeks ago"*|*"a week ago"*|*" months ago"*|Dead*) echo "$id" ;; esac
    done > /tmp/hc-containers.$$
  xargs -a /tmp/hc-containers.$$ -r -P 8 -n 20 sh -c 'timeout 300 docker rm -v "$@" > /dev/null 2>&1; true' _
  log "  stopped containers removed: $(wc -l < /tmp/hc-containers.$$)"
  # 2. per-run images older than 1 h
  timeout 300 docker images --filter "until=1h" --format '{{.Repository}}:{{.Tag}}' 2>/dev/null |
    grep -E '__[a-z0-9]{7}__' | grep -viE "$keep" > /tmp/hc-images.$$
  xargs -a /tmp/hc-images.$$ -r -P 4 -n 10 sh -c 'timeout 300 docker rmi "$@" > /dev/null 2>&1; true' _
  log "  per-run images removed (attempted): $(wc -l < /tmp/hc-images.$$)"
  # 3. gate-run folders older than 1 h, not used by a running gate
  ps -eo args | grep -o -- '--job-name [^ ]*' | awk '{print $2}' | sort -u > /tmp/hc-running.$$
  n=0
  for d in $(find "$HOME/.tb-graders/cwe/gate-jobs" -mindepth 1 -maxdepth 1 -type d -mmin +60 2>/dev/null); do
    grep -qx "$(basename "$d")" /tmp/hc-running.$$ && continue
    rm -rf "$d" 2>/dev/null || { chmod -R u+w "$d" 2>/dev/null; rm -rf "$d" 2>/dev/null; }
    n=$((n + 1))
  done
  log "  gate-run folders removed: $n"
  # 4-5. unused build cache and dangling images
  log "  build cache: $(timeout 1800 docker builder prune --all -f 2>&1 | tail -1)"
  # Dangling images are removed one by one, largest first: `docker image prune` on this containerd image store
  # (~27k images) computed for >7 min without deleting anything (2026-10-27); direct rmi frees space at once.
  # rmi without -f refuses any image a container still uses. Capped at 50 min per pass.
  timeout 300 docker images -f dangling=true --format '{{.ID}} {{.Size}}' 2>/dev/null |
    awk '{v=$2; u=v; gsub(/[0-9.]/,"",u); gsub(/[^0-9.]/,"",v); m=(u=="GB")?1000:(u=="MB")?1:(u=="kB")?0.001:0; print v*m, $1}' |
    sort -rn | awk '!s[$2]++ {print $2}' > /tmp/hc-dangling.$$
  timeout 3000 xargs -a /tmp/hc-dangling.$$ -r -P 6 -n 5 sh -c 'timeout 600 docker rmi "$@" > /dev/null 2>&1; true' _
  log "  dangling images removed (attempted, largest first): $(wc -l < /tmp/hc-dangling.$$)"
  rm -f /tmp/hc-dangling.$$
  # 6. shared task images unused for CWE_REUSE_KEEP_H hours (last use = mtime of the stamp each run touches)
  local used="${CWE_REUSE_STATE:-$HOME/.tb-graders/cwe/image-reuse}/used" keep_h=${CWE_REUSE_KEEP_H:-24}
  timeout 300 docker images --format '{{.Repository}}:{{.Tag}}' 'cwe-reuse/*' 2>/dev/null | grep -viE "$keep" |
    while read -r img; do
      st="$used/$(echo "$img" | tr '/:' '__')"
      [ -n "$(find "$st" -mmin -$((keep_h * 60)) 2>/dev/null)" ] && continue   # used recently (or right now)
      echo "$img"
    done > /tmp/hc-reuse.$$
  xargs -a /tmp/hc-reuse.$$ -r -P 4 -n 10 sh -c 'timeout 300 docker rmi "$@" > /dev/null 2>&1; true' _
  log "  shared task images unused > ${keep_h} h removed (attempted): $(wc -l < /tmp/hc-reuse.$$)"
  rm -f /tmp/hc-containers.$$ /tmp/hc-images.$$ /tmp/hc-running.$$ /tmp/hc-reuse.$$
  log "pass done: free $(freegb) GB"
}

case "${1:-}" in
  once) pass ;;
  loop)
    echo $$ > build/audit/hourly_cleanup.pid
    log "loop start (pid $$, every ${CLEANUP_EVERY_MIN:-60} min)"
    while true; do pass; sleep $(( ${CLEANUP_EVERY_MIN:-60} * 60 )); done ;;
  *) echo "usage: $0 once|loop" >&2; exit 2 ;;
esac
