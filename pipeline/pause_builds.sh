#!/bin/bash
# Pause building: stop every new-build launcher but leave in-flight builds, regate and trials alone.
cd "$HOME/cwe-bench" || exit 1
echo "=== pause builds $(date -u +%FT%TZ) ==="
before=$(ps -eo cmd | grep -cE '[r]un_build.sh .*-ds')
pkill -f 'xargs.*run_pipeline.sh deepseek' 2>/dev/null   # build feeders (main lane + both recovery)
pkill -f '[r]un_lane.sh deepseek' 2>/dev/null            # main controller wrapper
pkill -f 'abandoned_ds.txt' 2>/dev/null                  # recovery wrapper shells
pkill -f '[q]ueue.sh' 2>/dev/null                        # master queue (stops auto-advance to MiMo builds)
sleep 4
echo "stopped new-build launchers. In-flight DS builds finish; NO new builds will start."
echo "build feeders remaining (want 0): $(ps -eo cmd | grep -cE 'xargs.*run_pipeline|[r]un_lane.sh|[q]ueue.sh')"
echo "in-flight DS builds (finishing): $(ps -eo cmd | grep -cE '[r]un_build.sh .*-ds')  (was $before)"
echo "KEPT running: ds-trial-loop=$(ps -eo cmd | grep -c '[t]rial_set.sh') ds-trials=$(ps -eo cmd | grep -c '[t]rial.py.*deepseek')"
fin=$(for d in build/*-ds; do [ -f "$d/build-exit.txt" ] && echo 1; done 2>/dev/null | wc -l)
echo "DS built so far: $fin/50"
