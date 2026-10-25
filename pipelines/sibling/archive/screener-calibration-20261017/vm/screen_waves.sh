#!/bin/bash
# Run screener waves one model at a time on the VM; after each wave, copy its outputs back here
# and delete them from the VM, so a later wave cannot read an earlier one.
# Usage (on the Mac): screen_waves.sh STAGING LABEL [LABEL...]
set -euo pipefail
S=$1; shift
for L in "$@"; do
  echo "$(date -u +%T) start $L"
  ssh -o BatchMode=yes klavis-vm "cd ~/screen && rm -f wave-$L.done && cut -f1 hosts.tsv | xargs -P 9 -I{} ./run_screen.sh \$HOME/screen $L {} > wave-$L.log 2>&1; touch wave-$L.done; cat wave-$L.log"
  ssh -o BatchMode=yes klavis-vm "cd ~/screen && tar -cf - runs/$L wave-$L.log" | COPYFILE_DISABLE=1 tar -C "$S" -xf -
  n=$(ls "$S"/runs/$L/*/host.json 2>/dev/null | wc -l | tr -d ' ')
  ssh -o BatchMode=yes klavis-vm "rm -rf ~/screen/runs/$L"
  echo "$(date -u +%T) done $L: $n host.json copied back; removed from VM"
done
