"""CWE-918 SSRF: a webhook alert-channel URL pointing at an internal/private
host must be rejected when the channel is created. The server fetches this URL
later (signed POST) when an alert fires, so storing an internal URL lets a
tenant make the control plane call internal infrastructure.

Exploit entry point: POST /api/v1/projects/<ref>/alertChannels (PAT auth).
Vulnerable: the URL is stored unvalidated (HTTP 200). Fixed: the request is
rejected (HTTP 422). Several ranges/encodings are checked so a fix that blocks
only the cloud-metadata address still fails.
"""
import pytest
import tr

INTERNAL_URLS = [
    "http://169.254.169.254/latest/meta-data/",  # cloud metadata (link-local)
    "http://127.0.0.1:6379/",                     # loopback (internal Redis)
    "http://10.0.0.5/admin",                       # RFC1918 10/8
    "http://192.168.1.1/",                         # RFC1918 192.168/16
    "http://[::1]:8123/",                          # IPv6 loopback
    # 2026-10-16: the same targets written another way (the property is where the
    # destination resolves, not how it is spelled).
    "http://localhost:6379/",                      # name that resolves to loopback
    "http://2130706433/",                          # 127.0.0.1 as one decimal number
    "http://[::ffff:169.254.169.254]/latest/",     # IPv4-mapped IPv6 metadata address
]


@pytest.mark.parametrize("url", INTERNAL_URLS)
def test_internal_webhook_url_rejected(url):
    assert tr.PAT and tr.PROJREF, "fixtures not provided by test.sh"
    r = tr.create_alert_channel(url)
    assert 400 <= r["code"] < 500, (
        f"internal webhook url {url!r} was accepted (HTTP {r['code']}); "
        f"the server must refuse to store an SSRF-able alert webhook. "
        f"body={r['body'][:200]!r}"
    )
