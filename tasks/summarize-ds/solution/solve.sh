#!/bin/bash
# Reference fix: validate every URL that a feed or page asks the product to fetch
# (scheme, host name, IP literal ranges including IPv4-embedding IPv6 forms, DNS
# answers) and revalidate each redirect hop, at the transcript, caption, media,
# chapter and embedded-transcript fetch sites; complete the daemon's second copy of
# the address blocklist for the same IPv6 forms.
set -euo pipefail
cd /app
patch -p1 < /solution/fix.patch
