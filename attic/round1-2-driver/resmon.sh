#!/usr/bin/env bash
# Resource snapshot for adaptive parallelism (user, 2026-10-16: measure every 5-10 min).
# Prints one line: UTC, Docker disk free, VM memory available, VM load, running trial/gate containers.
disk=$(colima ssh -- df -BG /var/lib/docker 2>/dev/null | awk 'NR==2{print $4}')
mem=$(colima ssh -- awk '/MemAvailable/{printf "%.1fG", $2/1048576}' /proc/meminfo 2>/dev/null)
load=$(colima ssh -- cat /proc/loadavg 2>/dev/null | cut -d' ' -f1-3)
n=$(docker ps -q | wc -l | tr -d ' ')
echo "$(date -u +%FT%TZ) disk_free=$disk mem_avail=$mem load=[$load] containers=$n"
