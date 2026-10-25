#!/bin/bash
# Clean restart of the stacking queue on the FIXED pipeline (normalizer + check_stack + gate blind-exempt).
cd "$HOME/cwe-bench" || exit 1
L=stacking/out/queue/restart.log
{
echo "=== RESTART $(date -u +%FT%TZ) ==="
# 1. stop orchestrator
pkill -f "[s]tk_queue.py all" && echo "killed orchestrator" || echo "no orchestrator"
sleep 2
# 2. kill each build job's whole process group
for p in $(pgrep -f "[r]un_stack_pipeline.sh"); do kill -TERM -"$p" 2>/dev/null && echo "TERM grp $p"; done
sleep 6
for p in $(pgrep -f "[r]un_stack_pipeline.sh"); do kill -KILL -"$p" 2>/dev/null; done
pkill -9 -f "[r]un_stack_pipeline.sh" 2>/dev/null
pkill -9 -f "[g]ate.py stk-" 2>/dev/null
pkill -9 -f "[c]heck_stack.py stk-" 2>/dev/null
pkill -9 -f "[n]ormalize_expect.py stk-" 2>/dev/null
sleep 3
echo "after kill: queue=$(pgrep -fc '[s]tk_queue.py all') jobs=$(pgrep -fc '[r]un_stack_pipeline.sh') gatepy=$(pgrep -fc '[g]ate.py stk-')"
# 3. reset build state for all 30 slugs (+ controls) so nothing is skipped and rebuilds are clean
n=0
while read -r slug rest; do
  case "$slug" in \#*|"") continue;; esac
  rm -f  build/"$slug"/stack_pipeline.log build/"$slug"/manifest.json build/"$slug"/build-exit.txt \
         build/"$slug"/gate_report*.json build/"$slug"/.sound build/"$slug"/.unsound build/"$slug"/.auto_trialed 2>/dev/null
  rm -rf build/"$slug"/.lockdir build/"$slug"/harden_work build/"$slug"/exp \
         tasks/"$slug" tasks/"$slug"-control build/"$slug"-control 2>/dev/null
  n=$((n+1))
done < stacking/out/batch1.txt
echo "reset $n slugs"
# 4. relaunch (all = build phase then auto-advance to trial phase)
: > stacking/out/queue/nohup.log
setsid nohup python3 -I stacking/stk_queue.py all --slugs-file stacking/out/batch1.txt >> stacking/out/queue/nohup.log 2>&1 < /dev/null &
echo "relaunched pid=$!"
echo "=== RESTART DONE $(date -u +%FT%TZ) ==="
} >> "$L" 2>&1
