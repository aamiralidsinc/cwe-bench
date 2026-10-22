#!/bin/bash
cd /home/mara/cwe-bench || exit 1
for i in 1 2 3 4 5 6; do
  echo "[patches-retry] attempt $i $(date -u +%T)" >> build/astro-ds/gate-patches2.log
  python3 -I builder/gate.py astro-ds --only patches >> build/astro-ds/gate-patches2.log 2>&1
  rc=$?
  echo "[patches-retry] attempt $i exit $rc $(date -u +%T)" >> build/astro-ds/gate-patches2.log
  if grep -q "PASSED (patches only)" build/astro-ds/gate-patches2.log; then exit 0; fi
  sleep 60
done
exit 1
