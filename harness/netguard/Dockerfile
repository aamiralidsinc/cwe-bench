# netguard: per-trial egress sidecar that enforces the client's trial rule "internet, but no access
# to the task's own repository" (2026-10-16). The task's main container joins this container's
# network namespace (network_mode: service:netguard); see README.md.
FROM mitmproxy/mitmproxy:11.1.3
USER root
RUN apt-get update && apt-get install -y --no-install-recommends nftables ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 64999 --no-create-home --shell /usr/sbin/nologin netguard
COPY entrypoint.sh guard.py /opt/netguard/
RUN chmod 755 /opt/netguard/entrypoint.sh
ENTRYPOINT ["/opt/netguard/entrypoint.sh"]
