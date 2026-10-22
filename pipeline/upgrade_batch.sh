#!/bin/bash
# Upgrade batch: 35 sound non-breaker -ds tasks to §2-§8, DeepSeek-driven, P5 sliding window.
# Each: snapshot v1 (provenance) -> upgrade edits -> CONDITIONAL gate (static-only if instruction-only).
cd "$HOME/cwe-bench" || exit 1
LOG=build/pipeline/upgrade_batch.log
SET="airflow-ds arc-ds ckan-mcp-server-ds compliance-trestle-ds django-cms-ds ec2-fleet-plugin-ds fission-ds flowise-ds ghost-ds gogs-ds grav-ds hazelcast-ds hermes-agent-ds hubuum-client-rust-ds jetty.project-ds langchain-ds limesurvey-ds mcp-atlassian-ds mockoon-ds n8n-ds new-api-ds pimcore-ds portainer-ds prompty-ds protobuf.js-ds rsdoctor-ds seaweedfs-ds siyuan-ds summarize-ds surrealdb-ds theia-ds traefik-ds typo3-ds vitest-ds whistle-ds"
{
echo "=== upgrade_batch START $(date -u +%FT%TZ) : $(echo $SET | wc -w) tasks, P5 sliding window ==="
printf '%s\n' $SET | xargs -P5 -I{} bash -c 'cd "$HOME/cwe-bench"; ./drive.sh deepseek bash run_upgrade.sh "$1" >> "build/$1/upgrade.nohup" 2>&1; echo "[done $1 $(date -u +%T)] $(tail -1 build/$1/upgrade-gate.log 2>/dev/null)"' _ {}
echo "=== upgrade_batch DONE $(date -u +%FT%TZ) ==="
echo ALL-UPGRADE-DONE
} >> "$LOG" 2>&1
