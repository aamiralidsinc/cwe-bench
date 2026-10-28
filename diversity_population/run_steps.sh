#!/usr/bin/env bash
# Steps 1-4 on the source pool, with the COPIED sourcer and the experiment's own index and data folder:
#   1 diffs, 2 classify (diffs + classify again, for fix commits that classify moved to a pool entry),
#   3 parents, 4 repo-meta (GitHub's unauthenticated limit: 55 repos per run, one run an hour).
# Progress: out/steps.log (stage output), out/steps_status.txt (current stage + heartbeat every 30 s).
# Resumable: every stage skips work it already did.
set -u
cd "$(dirname "$0")/.."
D=diversity_population
S="python3 -I $D/copied/sourcer/osv_sourcer.py --data $HOME/.tb-graders/cwe/diversity-data --index $D/out/index/candidates.sqlite"
LOG=$D/out/steps.log; ST=$D/out/steps_status.txt
stage() { echo "$(date -u +%FT%TZ) $1" > $ST; echo "=== $(date -u +%FT%TZ) $1" >> $LOG; }
( while sleep 30; do [ -f $ST ] && touch $ST; done ) & HB=$!
trap 'kill $HB 2>/dev/null' EXIT

stage "1 diffs";              $S diffs --delay 1.2 >> $LOG 2>&1 || echo "diffs exit $?" >> $LOG
stage "2 classify";           $S classify >> $LOG 2>&1 || echo "classify exit $?" >> $LOG
stage "1b diffs (moved)";     $S diffs --delay 1.2 >> $LOG 2>&1 || echo "diffs exit $?" >> $LOG
stage "2b classify";          $S classify >> $LOG 2>&1 || echo "classify exit $?" >> $LOG
stage "3 parents";            $S parents --limit 5000 --delay 1.5 >> $LOG 2>&1 || echo "parents exit $?" >> $LOG
for i in $(seq 1 18); do
  left=$(sqlite3 $D/out/index/candidates.sqlite "select count(distinct repo) from entries where status in ('candidate','shortlisted') and repo_stars is null")
  stage "4 repo-meta run $i ($left repos left)"
  [ "$left" -eq 0 ] && break
  $S repo-meta --limit 55 >> $LOG 2>&1 || echo "repo-meta exit $?" >> $LOG
  now=$(sqlite3 $D/out/index/candidates.sqlite "select count(distinct repo) from entries where status in ('candidate','shortlisted') and repo_stars is null")
  [ "$now" -eq 0 ] && break
  [ "$now" -ge "$left" ] && { echo "repo-meta made no progress ($now left); stopping" >> $LOG; break; }
  sleep 3700
done
stage "done"
