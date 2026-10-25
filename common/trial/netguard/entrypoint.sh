#!/bin/sh
# Starts the filtering proxy, publishes its CA to the shared volume, then switches on nftables.
# Only processes running as uid 64999 (the proxy) may reach the internet directly.
set -eu
CERTS=/netguard-certs            # shared read-only into the main container
CONF=/home/netguard-conf
mkdir -p "$CERTS" "$CONF"; chown 64999 "$CONF"
rm -f /tmp/netguard.ready

# 1. Proxy (transparent mode, as uid 64999). It writes its CA into $CONF on first start.
su -s /bin/sh netguard -c "mitmdump --mode transparent --listen-port 8080 --showhost \
  --set confdir=$CONF --set block_global=false --set connection_strategy=lazy \
  -s /opt/netguard/guard.py" &
PROXY=$!
for i in $(seq 1 50); do [ -f "$CONF/mitmproxy-ca-cert.pem" ] && break; sleep 0.2; done
[ -f "$CONF/mitmproxy-ca-cert.pem" ] || { echo "netguard: proxy did not create its CA" >&2; exit 1; }

# 2. Trust bundle for the main container: system roots + this trial's CA.
cp "$CONF/mitmproxy-ca-cert.pem" "$CERTS/netguard-ca.pem"
cat /etc/ssl/certs/ca-certificates.crt "$CERTS/netguard-ca.pem" > "$CERTS/bundle.pem"
chmod 644 "$CERTS"/*

# 3. Enforcement. Loopback and the container's own addresses stay open (local services, tests).
nft -f - <<NFT
table inet netguard
delete table inet netguard
table inet netguard {
  chain nat_out {
    type nat hook output priority -100; policy accept;
    meta skuid 64999 accept
    fib daddr type local accept
    ip daddr 127.0.0.0/8 accept
    tcp dport { 80, 443 } redirect to :8080
  }
  chain filter_out {
    type filter hook output priority 0; policy accept;
    meta skuid 64999 accept
    oifname "lo" accept
    fib daddr type local accept
    udp dport 53 accept
    tcp dport 53 accept
    tcp dport 8080 accept
    meta l4proto { tcp, udp } reject
  }
}
NFT
echo "netguard: ready (blocking repos=${NETGUARD_BLOCK_REPOS:-} names=${NETGUARD_BLOCK_NAMES:-})"
touch /tmp/netguard.ready
wait $PROXY
