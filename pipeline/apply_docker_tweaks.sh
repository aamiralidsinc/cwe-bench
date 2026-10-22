#!/bin/bash
# Apply CWE-bench Docker tuning + restart, detached-safe (survives ssh drops).
cd "$HOME/cwe-bench" || exit 1
LOG="pipeline/apply_docker_tweaks.log"
exec >>"$LOG" 2>&1
echo "=== apply_docker_tweaks START $(date -u +%FT%TZ) ==="

# 1. Stop the in-flight gates (+ their trial.py children). No set -e: pkill may return 1.
pkill -f "builder/gate.py"; pkill -f "build/trial.py"; sleep 4
echo "[1] after kill: gate.py=$(pgrep -fc gate.py) trial.py=$(pgrep -fc trial.py)"

# 2. daemon.json: keep address pools; add shutdown-timeout + raised nofile ulimits.
sudo cp /etc/docker/daemon.json "/etc/docker/daemon.json.bak-$(date -u +%Y%m%dT%H%M%SZ)"
sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "default-address-pools": [
    { "base": "172.16.0.0/12", "size": 24 }
  ],
  "shutdown-timeout": 120,
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Soft": 1048576, "Hard": 1048576 }
  }
}
JSON
python3 -c "import json;json.load(open('/etc/docker/daemon.json'));print('[2] daemon.json valid JSON')" || { echo "[2] BAD JSON - aborting restart"; exit 1; }

# 3. Compose/client timeouts, sourced by the launchers (durable for future runs).
cat > pipeline/docker-tuning.env <<'ENV'
# Raised Docker client/compose timeouts: a busy daemon returns "slow" not "failed",
# which kills the context-deadline-exceeded compose flakes under concurrency.
export COMPOSE_HTTP_TIMEOUT=300
export DOCKER_CLIENT_TIMEOUT=300
ENV
SRC='. "$HOME/cwe-bench/pipeline/docker-tuning.env" 2>/dev/null || true'
for f in pipeline/run_pipeline.sh harness/run_trial.sh pipeline/gate_one_ds.sh; do
  if [ -f "$f" ] && ! grep -q docker-tuning.env "$f"; then
    awk -v s="$SRC" 'NR==1{print; print s; next} {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f" && chmod +x "$f"
    echo "[3] sourced docker-tuning.env into $f"
  fi
done

# 4. Restart docker (kills orphaned gate containers -> clean slate).
echo "[4] restarting docker $(date -u +%FT%TZ)"
sudo systemctl restart docker
sleep 12
echo "[4] docker=$(docker info --format '{{.ServerVersion}}' 2>&1) containers=$(docker ps -q | wc -l)"
echo "=== apply_docker_tweaks DONE $(date -u +%FT%TZ) ==="
