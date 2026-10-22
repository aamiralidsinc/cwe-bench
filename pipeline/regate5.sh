#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
LOG=build/pipeline/regate_groupA.log
: > "$LOG"
echo "=== serialized re-gate Group-A START $(date -u +%FT%TZ) ===" >> "$LOG"

# --- portainer keeper net + container (idempotent) ---
if ! docker network inspect portainer-ds-fixed-net >/dev/null 2>&1; then
  docker network create portainer-ds-fixed-net >> "$LOG" 2>&1 && echo "[keeper] created portainer-ds-fixed-net" >> "$LOG"
fi
if ! docker ps --format '{{.Names}}' | grep -q '^portainer-ds-net-keeper$'; then
  KIMG=""
  for img in busybox:latest alpine:latest node:24-bookworm-slim; do docker image inspect "$img" >/dev/null 2>&1 && KIMG="$img" && break; done
  [ -z "$KIMG" ] && KIMG=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -vi '<none>' | head -1)
  docker run -d --name portainer-ds-net-keeper --restart unless-stopped --network portainer-ds-fixed-net "$KIMG" sleep infinity >> "$LOG" 2>&1 \
    && echo "[keeper] started keeper ($KIMG) on portainer-ds-fixed-net" >> "$LOG" \
    || echo "[keeper] FAILED to start keeper (img=$KIMG)" >> "$LOG"
fi

# --- serialized re-gate (ONE AT A TIME defeats the prune race) ---
for s in astro-ds flyto-core-ds keras-ds fission-ds portainer-ds; do
  echo "--- re-gate $s $(date -u +%T) ---" >> "$LOG"
  bash pipeline/gate_one_ds.sh "$s" >> "$LOG" 2>&1
  if [ -f build/$s/.sound ] && [ ! -f build/$s/.unsound ]; then echo "[RESULT $s] SOUND" >> "$LOG"
  else echo "[RESULT $s] STILL UNSOUND" >> "$LOG"; fi
done
echo "=== DONE $(date -u +%FT%TZ) ===" >> "$LOG"
echo "REGATE-GROUPA-DONE" >> "$LOG"
