#!/bin/bash
# Make every built DS task trial-ready: gate every one that isn't .sound yet (covers both the
# false-'unsound' compose flakes and the 'neither' never-gated), at concurrency C, with retries.
C=${1:-3}
cd "$HOME/cwe-bench" || exit 1
L=build/pipeline/recover_all.list
: > "$L"
for d in build/*-ds; do
  s=$(basename "$d")
  [ -f "$d/build-exit.txt" ] || continue
  [ -e "$d/.sound" ] && continue
  [ "$(find "tasks/$s" -type f 2>/dev/null | wc -l)" -lt 5 ] && continue
  echo "$s" >> "$L"
done
n=$(grep -c . "$L" || echo 0)
echo "=== regate_all_ds $(date -u +%FT%TZ): recovering $n non-sound DS tasks at C=$C ==="
[ "$n" = 0 ] && exit 0
cat "$L" | xargs -P "$C" -I {} bash pipeline/gate_one_ds.sh {}
echo "=== done $(date -u +%FT%TZ): .sound=$(ls build/*-ds/.sound 2>/dev/null | wc -l) .unsound=$(ls build/*-ds/.unsound 2>/dev/null | wc -l) ==="
