#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/regate_serial.log; : > "$LOG"
echo "=== STRICT-SERIAL re-gate START $(date -u +%FT%TZ) (one at a time, no concurrent gates) ===" >> "$LOG"
for s in astro-ds keras-ds flyto-core-ds fission-ds; do
  echo "--- $s $(date -u +%T) ---" >> "$LOG"
  bash pipeline/gate_one_ds.sh "$s" >> "$LOG" 2>&1
  if [ -f build/$s/.sound ] && [ ! -f build/$s/.unsound ]; then echo "[RESULT $s] SOUND" >> "$LOG"
  else echo "[RESULT $s] STILL UNSOUND ($(grep -oiE "network .* not found|build failed|patches=None|nop=None|oracle=None" build/$s/recover.log 2>/dev/null|tail -1))" >> "$LOG"; fi
done
echo "REGATE-SERIAL-DONE $(date -u +%FT%TZ)" >> "$LOG"
