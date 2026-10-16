#!/usr/bin/env bash
# Exit when any experiment trial log gains a new result line, or after MAX seconds (heartbeat).
cd /Users/dev/terminal-bench/cwe-bench/build/exp
MAX=${1:-1200}
before=$(cat *.out 2>/dev/null | grep -c 'reward=')
for ((i=0; i<MAX; i+=20)); do
  now=$(cat *.out 2>/dev/null | grep -c 'reward=')
  if [ "$now" != "$before" ]; then echo "NEW RESULT"; grep -H 'reward=' *.out | tail -20; exit 0; fi
  sleep 20
done
echo "HEARTBEAT (no new results in ${MAX}s)"; ../resmon.sh
