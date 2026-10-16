#!/bin/bash
# 2026-10-16: finish the trigger-dev regrades cut off by a session restart, then start the 3
# rclone-sib MiMo runs (repaired correct-secret proxy tests; gate passed 19:03). Detached via setsid.
cd /Users/dev/terminal-bench/cwe-bench
WHY="2026-10-16: tests repaired (realtime write any 4xx, own-batch check-completion fixture, exact statuses relaxed); Eyc3WUE = control (solved originally)"
for t in trigger-dev-deepseek-r4-20261015-135410-n001/trigger-dev__eQ9xLN3 trigger-dev-deepseek-r3-20261015-131852-n004/trigger-dev__Eyc3WUE; do
  python3 build/regrade_from_code.py ~/.tb-graders/cwe/jobs/$t "$WHY" > build/trigger-dev/regrade-$(basename $t)-20261016.log 2>&1
done
for n in 4 5 6; do
  caffeinate -i python3 build/trial.py rclone-sib --models mimo --max-runs 1 --first-run $n --full --no-verdict > build/rclone-sib/rerun-mimo-r$n-20261016.log 2>&1 &
  sleep 20
done
wait
