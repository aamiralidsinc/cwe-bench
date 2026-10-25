#!/bin/bash
mkdir -p /logs/verifier; cp /app/net.txt /logs/verifier/net.txt 2>/dev/null
ok=1
for h in deepseek mimo; do c=$(awk -v h=$h '$1==h{print $2}' /app/net.txt); [ "$c" != "000" ] && [ -n "$c" ] || ok=0; done
for h in github raw pypi plain; do c=$(awk -v h=$h '$1==h{print $2}' /app/net.txt); [ "$c" = "000" ] || ok=0; done
grep -q "git blocked" /app/net.txt || ok=0; grep -q "ssh blocked" /app/net.txt || ok=0; grep -q "smtp blocked" /app/net.txt || ok=0
echo $ok > /logs/verifier/reward.txt; printf '{"reward": %s}\n' $ok > /logs/verifier/reward.json
