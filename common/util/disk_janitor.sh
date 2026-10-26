#!/bin/bash
# disk_janitor.sh : disk cleanup for long runs, ALWAYS with the owner's approval (owner decision 2026-10-26).
#
#   bash common/util/disk_janitor.sh report [keep_gate_hours] [keep_tmp_hours]
#        lists what WOULD be removed and writes build/audit/janitor/report-<UTC>.txt (+ candidates-<UTC>.list).
#        Nothing is deleted.
#   bash common/util/disk_janitor.sh loop [every_hours]
#        writes such a report every <every_hours> (default 6); still deletes nothing.
#   bash common/util/disk_janitor.sh apply <candidates-<UTC>.list>
#        deletes exactly the paths in that list (re-checking each is still old and not in use). Run only after the
#        owner approved that report.
#
# Candidates: Harbor gate-run folders (~/.tb-graders/cwe/gate-jobs/*) older than <keep_gate_hours> (default 12), and
# /tmp entries older than <keep_tmp_hours> (default 6), except system folders, containerd-mount*, and anything a running
# process uses. Gate verdicts, reports and evidence live in build/<slug>/ and trial runs in ~/.tb-graders/cwe/jobs:
# neither is ever a candidate. Why: on 2026-10-26 gate-jobs reached 850 GB in a day, and /tmp (a tmpfs with ~1M file
# entries) filled up with test-suite leftovers until a gate failed with "No space left on device".
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
D="$CWE_ROOT/build/audit/janitor"; mkdir -p "$D"
SKIP_TMP='^(\.X11-unix|\.ICE-unix|\.XIM-unix|\.font-unix|\.Test-unix|containerd-mount.*|systemd-private-.*|snap-private-tmp)$'

in_use() {   # top-level names under /tmp and gate-jobs that a running process uses (cwd or arguments)
  for p in $(ls /proc | grep -E '^[0-9]+$'); do
    { readlink /proc/$p/cwd; tr '\0' '\n' < /proc/$p/cmdline; } 2>/dev/null   # processes may exit mid-scan
  done | grep -oE '^/tmp/[^/ ]+|gate-jobs/[^/ ]+' | sed 's|^/tmp/|tmp:|; s|^gate-jobs/|gate:|' | sort -u
}

report() {
  local KG=${1:-12} KT=${2:-6} T; T=$(date -u +%Y%m%dT%H%M%SZ)
  local L="$D/candidates-$T.list" R="$D/report-$T.txt" use; use=$(in_use)
  : > "$L"
  find "$HOME/.tb-graders/cwe/gate-jobs" -mindepth 1 -maxdepth 1 -mmin +$((KG*60)) -print 2>/dev/null | while read -r p; do
    printf '%s\n' "$use" | grep -qx "gate:$(basename "$p")" || echo "$p"; done >> "$L"
  find /tmp -mindepth 1 -maxdepth 1 -mmin +$((KT*60)) -print 2>/dev/null | while read -r p; do
    b=$(basename "$p"); [[ "$b" =~ $SKIP_TMP ]] && continue
    printf '%s\n' "$use" | grep -qx "tmp:$b" || echo "$p"; done >> "$L"
  local ng nt; ng=$(grep -c "/gate-jobs/" "$L"); nt=$(grep -c "^/tmp/" "$L")
  {
    echo "Janitor report $T (nothing deleted). Approve, then: bash common/util/disk_janitor.sh apply $L"
    echo "disk /      : $(df -h / | tail -1 | awk '{print $4" free of "$2" ("$5" used)"}')"
    echo "tmpfs /tmp  : $(df -h /tmp | tail -1 | awk '{print $3" used of "$2}'), file entries $(df -i /tmp | tail -1 | awk '{print $3" of "$2" ("$5")"}')"
    echo "candidates  : $ng gate-run folders older than ${KG} h ($(grep "/gate-jobs/" "$L" | head -2000 | xargs -r du -sc 2>/dev/null | tail -1 | cut -f1 | awk '{printf "%.0f GB (first 2000)", $1/1048576}')), $nt /tmp entries older than ${KT} h"
    echo "oldest gate : $(grep "/gate-jobs/" "$L" | xargs -r ls -dt 2>/dev/null | tail -1 | xargs -r stat -c '%y %n' 2>/dev/null | cut -c1-16,36-)"
    echo "newest gate : $(grep "/gate-jobs/" "$L" | xargs -r ls -dt 2>/dev/null | head -1 | xargs -r stat -c '%y %n' 2>/dev/null | cut -c1-16,36-)"
    echo "/tmp sample : $(grep "^/tmp/" "$L" | head -8 | xargs -r -n1 basename | tr '\n' ' ')"
  } > "$R"
  ln -sf "$R" "$D/LATEST_REPORT.txt"
  cat "$R"
}

case "${1:-report}" in
  report) shift; report "$@" ;;
  loop) EV=${2:-6}; while true; do report >/dev/null; sleep $((EV*3600)); done ;;
  apply)
    L=${2:?usage: disk_janitor.sh apply <candidates list>}; [ -f "$L" ] || { echo "no list $L"; exit 2; }
    use=$(in_use); n=0; before=$(df -BG / | tail -1 | awk '{print $4}')
    while read -r p; do
      [ -e "$p" ] || continue
      case "$p" in "$HOME/.tb-graders/cwe/gate-jobs/"*) k="gate:$(basename "$p")";; /tmp/*) k="tmp:$(basename "$p")";; *) continue;; esac
      printf '%s\n' "$use" | grep -qx "$k" && continue
      nice -n 19 ionice -c3 rm -rf "$p"; n=$((n+1))
    done < "$L"
    msg="$(date -u +%FT%TZ) applied $(basename "$L"): removed $n paths; disk free $before -> $(df -BG / | tail -1 | awk '{print $4}'); /tmp entries $(df -i /tmp | tail -1 | awk '{print $5}')"
    echo "$msg" | tee -a "$D/applied.log" ;;
  *) echo "usage: disk_janitor.sh report|loop|apply" ; exit 2 ;;
esac
