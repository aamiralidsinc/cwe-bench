#!/bin/bash
# Fully undo the retrial_stage: kill only its processes (NOT litellm r4, NOT siyuan fairfix),
# restore the archived pre-fairfix run-folders, remove any new partial retrial folders.
cd "$HOME/cwe-bench" || exit 1
ARCH="$HOME/.tb-graders/cwe/jobs/_pre-fairfix-archive"
SOUND="protobuf.js-ds airflow-ds hazelcast-ds hermes-agent-ds"
NONSOUND="prompty-path-read-inj flowise-cross-tenant-inj vitest-api-fs-authz-inj"
{
echo "=== UNDO retrial_stage $(date -u +%FT%TZ) ==="
pkill -9 -f "[r]etrial_stage"
for s in $SOUND; do pkill -9 -f "[t]rial.py $s"; done
for s in $NONSOUND; do pkill -9 -f "[g]ate_one_ds.sh $s"; pkill -9 -f "[g]ate.py $s"; done
sleep 4
# remove NEW partial retrial job folders (created in the last 20 min) for the 4 sound slugs
for s in $SOUND; do
  for jd in $(find "$HOME/.tb-graders/cwe/jobs" -maxdepth 1 -type d -name "${s}-deepseek-*" -mmin -20 2>/dev/null); do rm -rf "$jd"; echo "  removed new retrial folder: $(basename $jd)"; done
done
# restore archived pre-fairfix run-folders
n=0; if [ -d "$ARCH" ]; then for jd in "$ARCH"/*; do [ -e "$jd" ] || continue; mv "$jd" "$HOME/.tb-graders/cwe/jobs/" 2>/dev/null && n=$((n+1)); done; rmdir "$ARCH" 2>/dev/null; fi
echo "restored $n archived run-folders"
echo "litellm r4 alive? $(pgrep -cf '[t]rial.py litellm') (want >=1) | siyuan fairfix alive? $(pgrep -cf '[r]un_fairfix.sh')"
echo "retrial trials still alive? $(pgrep -cf '[t]rial.py protobuf|[t]rial.py airflow|[t]rial.py hazelcast|[t]rial.py hermes') (want 0)"
echo "=== UNDO DONE $(date -u +%FT%TZ) ==="
} >> build/pipeline/undo_retrial.log 2>&1
cat build/pipeline/undo_retrial.log
