#!/bin/bash
# Runs in the AGENT phase: record what is reachable.
r() { c=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$1"); echo "$2 $c"; }
{
r https://api.deepseek.com/anthropic/v1/messages deepseek
r https://api.xiaomimimo.com/anthropic/v1/messages mimo
r https://github.com/rclone/rclone github
r https://raw.githubusercontent.com/minio/minio/master/README.md raw
r https://pypi.org/simple/requests/ pypi
r https://example.com/ plain
git ls-remote https://github.com/minio/mc >/dev/null 2>&1 && echo "git ok" || echo "git blocked"
b=$(timeout 10 bash -c 'exec 3<>/dev/tcp/github.com/22; head -c 7 <&3' 2>/dev/null); [ "$b" = "SSH-2.0" ] && echo "ssh ok (banner: $b)" || echo "ssh blocked (no banner)"
b=$(timeout 10 bash -c 'exec 3<>/dev/tcp/smtp.gmail.com/587; head -c 3 <&3' 2>/dev/null); [ "$b" = "220" ] && echo "smtp ok" || echo "smtp blocked"
} > /app/net.txt 2>&1
