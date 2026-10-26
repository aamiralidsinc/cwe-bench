"""Credentials must not follow a redirect to another origin (control: the reported route)."""

from __future__ import absolute_import

from urllib3 import PoolManager, ProxyManager
from urllib3.util.retry import Retry

from support.harness import RecordingServer

AUTHORIZATION = {"Authorization": "Bearer marker-auth-7f3a"}
TIMEOUT = 10


def test_cross_host_redirect_withholds_authorization():
    with RecordingServer() as origin, RecordingServer() as other:
        origin.redirect("/start", "http://localhost:%d/next" % other.port)
        other.ok("/next")
        response = PoolManager().request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                         headers=dict(AUTHORIZATION), timeout=TIMEOUT)
        assert response.status == 200
        assert other.requests_to("/next"), "the redirect target was never reached"
        assert other.received("/next", "Authorization") is None


def test_cross_port_redirect_withholds_authorization():
    with RecordingServer() as origin, RecordingServer() as other:
        origin.redirect("/start", "http://127.0.0.1:%d/next" % other.port)
        other.ok("/next")
        response = PoolManager().request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                         headers=dict(AUTHORIZATION), timeout=TIMEOUT)
        assert response.status == 200
        assert other.requests_to("/next"), "the redirect target was never reached"
        assert other.received("/next", "Authorization") is None


def test_configured_credentials_are_not_forwarded_to_another_host():
    with RecordingServer() as origin, RecordingServer() as other:
        origin.redirect("/start", "http://localhost:%d/next" % other.port)
        other.ok("/next")
        client = PoolManager(headers=dict(AUTHORIZATION))
        response = client.request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                  timeout=TIMEOUT)
        assert response.status == 200
        assert other.requests_to("/next"), "the redirect target was never reached"
        assert other.received("/next", "Authorization") is None


def test_proxied_cross_origin_redirect_withholds_authorization():
    with RecordingServer() as proxy:
        proxy.redirect("http://127.0.0.1:65001/start", "http://127.0.0.1:65002/next")
        proxy.ok("http://127.0.0.1:65002/next")
        client = ProxyManager("http://127.0.0.1:%d" % proxy.port)
        response = client.request("GET", "http://127.0.0.1:65001/start",
                                  headers=dict(AUTHORIZATION), timeout=TIMEOUT)
        assert response.status == 200
        assert proxy.requests_to("http://127.0.0.1:65002/next"), \
            "the redirect target was never requested"
        assert proxy.received("http://127.0.0.1:65002/next", "Authorization") is None


def test_retrying_redirect_withholds_credentials():
    with RecordingServer() as origin, RecordingServer() as other:
        origin.redirect("/start", "http://127.0.0.1:%d/next" % other.port)
        other.ok("/next")
        client = PoolManager(retries=Retry(total=3))
        response = client.request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                  headers=dict(AUTHORIZATION), timeout=TIMEOUT)
        assert response.status == 200
        assert other.requests_to("/next"), "the redirect target was never reached"
        assert other.received("/next", "Authorization") is None
