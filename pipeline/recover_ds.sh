#!/bin/bash
# recover_ds.sh [concurrency] — rebuild DS tasks that were started then killed (stale .lockdir +
# pipeline.log but no build-exit.txt and no running build). They were abandoned in a cutback and
# the skip-guard will never rebuild them, so reset and build them fresh.
set -uo pipefail
C=${1:-6}
cd "$HOME/cwe-bench" || exit 1
LIST=build/pipeline/abandoned_ds.txt
: > "$LIST"
for d in build/*-ds; do
  s=$(basename "$d")
  [ -f "$d/pipeline.log" ] || continue           # never started -> the controller still owns it
  [ -f "$d/build-exit.txt" ] && continue          # finished building
  pgrep -f "run_build.sh $s" >/dev/null 2>&1 && continue   # currently building
  echo "$s" >> "$LIST"
done
n=$(grep -c . "$LIST" || true)
echo "abandoned DS tasks to rebuild: $n"
[ "$n" = 0 ] && exit 0
while read -r s; do
  [ -n "$s" ] || continue
  rm -rf "build/$s/.lockdir" "build/$s/pipeline.log" "build/$s/.unsound" "build/$s/.sound" \
         "build/$s/build-run.json" "build/$s/build-run.err" "tasks/$s"
done < "$LIST"
echo "reset done; launching recovery build at width $C"
nohup bash -c 'cat '"$LIST"' | xargs -P '"$C"' -I {} bash pipeline/run_pipeline.sh deepseek {}' \
  > build/pipeline/recover_ds.log 2>&1 < /dev/null &
echo "recovery build pid $!"
