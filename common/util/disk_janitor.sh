#!/bin/bash
# disk_janitor.sh [every_hours] [keep_hours] : periodic disk cleanup for long runs (owner decision 2026-10-26).
# Every <every_hours> (default 6): delete Harbor gate-run folders (~/.tb-graders/cwe/gate-jobs/*) older than
# <keep_hours> (default 12) and /tmp/gate-* copies older than 6 h. Each task's gate verdict, reports and evidence live in
# build/<slug>/ and are never touched; trial runs (~/.tb-graders/cwe/jobs) are never touched. Folders a running process
# still uses are skipped. Log: build/audit/disk_janitor.log. On 2026-10-26 gate-jobs reached 850 GB in a day.
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
EVERY=${1:-6}; KEEP=${2:-12}; L="$CWE_ROOT/build/audit/disk_janitor.log"
while true; do
  before=$(df -BG / | tail -1 | awk '{print $4}')
  busy=$(for p in $(pgrep -f "harbor|gate.py" 2>/dev/null); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -o "gate-jobs/[^ /]*"; done | sort -u)
  n=0
  while IFS= read -r -d '' d; do
    b="gate-jobs/$(basename "$d")"; printf '%s\n' "$busy" | grep -qx "$b" && continue
    nice -n 19 ionice -c3 rm -rf "$d"; n=$((n+1))
  done < <(find "$HOME/.tb-graders/cwe/gate-jobs" -mindepth 1 -maxdepth 1 -mmin +$((KEEP*60)) -print0 2>/dev/null)
  find /tmp -maxdepth 1 -name 'gate-*' -mmin +360 -print0 2>/dev/null | xargs -0 -r rm -rf
  echo "$(date -u +%FT%TZ) removed $n gate-run folders older than ${KEEP}h; free $before -> $(df -BG / | tail -1 | awk '{print $4}')" >> "$L"
  sleep $((EVERY*3600))
done
