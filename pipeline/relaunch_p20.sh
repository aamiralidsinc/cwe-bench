#!/bin/bash
# Stop the P5 upgrade queue (leave in-flight upgrades running), then relaunch the NOT-YET-STARTED
# target tasks at P20 with a per-worker start jitter (stagger -> no cold-fill sshd starve).
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/upgrade_batch.log
# stop only the P5 orchestrator (not the run_upgrade/drive/claude workers already mid-edit)
pkill -9 -f "[u]pgrade_batch.sh"; pkill -9 -f "[x]args -P5 -I"
sleep 3
TARGET="airflow-ds arc-ds ckan-mcp-server-ds compliance-trestle-ds django-cms-ds ec2-fleet-plugin-ds fission-ds flowise-ds ghost-ds gogs-ds grav-ds hazelcast-ds hermes-agent-ds hubuum-client-rust-ds jetty.project-ds langchain-ds limesurvey-ds mcp-atlassian-ds mockoon-ds n8n-ds new-api-ds pimcore-ds portainer-ds prompty-ds protobuf.js-ds rsdoctor-ds seaweedfs-ds siyuan-ds summarize-ds surrealdb-ds theia-ds traefik-ds typo3-ds vitest-ds whistle-ds"
REMAIN=""
for s in $TARGET; do
  [ -f "build/$s/upgrade_start.txt" ] && continue   # already started (in-flight or done) -> skip
  REMAIN="$REMAIN $s"
done
{
echo "=== relaunch P20 (staggered) $(date -u +%FT%TZ): in-flight kept, $(echo $REMAIN | wc -w) remaining at P20 ==="
echo "remaining: $REMAIN"
printf '%s\n' $REMAIN | xargs -P20 -I{} bash -c 'sleep $(( RANDOM % 30 )); cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_upgrade.sh "$1" >> "build/$1/upgrade.nohup" 2>&1; echo "[done $1 $(date -u +%T)] $(tail -1 build/$1/upgrade-gate.log 2>/dev/null)"' _ {}
echo "=== relaunch P20 DONE $(date -u +%FT%TZ) ==="
echo ALL-UPGRADE-DONE-P20
} >> "$LOG" 2>&1
