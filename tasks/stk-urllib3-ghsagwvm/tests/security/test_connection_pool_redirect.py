"""Credentials must not follow a redirect to another origin (connection-pool entry point)."""

from __future__ import absolute_import

from urllib3 import HTTPConnectionPool

from support.harness import RecordingServer

AUTHORIZATION = {"Authorization": "Bearer marker-auth-2c81"}
COOKIE = {"Cookie": "session=marker-cookie-4d6e"}


def _pool_as_proxy(proxy):
    return HTTPConnectionPool("127.0.0.1", proxy.port)


def test_foreign_host_redirect_withholds_authorization():
    with RecordingServer() as proxy:
        proxy.redirect("http://127.0.0.1:65011/start", "http://127.0.0.1:65012/next")
        proxy.ok("http://127.0.0.1:65012/next")
        pool = _pool_as_proxy(proxy)
        try:
            response = pool.urlopen("GET", "http://127.0.0.1:65011/start",
                                    headers=dict(AUTHORIZATION), assert_same_host=False,
                                    redirect=True, timeout=10)
        finally:
            pool.close()
        assert response.status == 200
        assert proxy.requests_to("http://127.0.0.1:65012/next"), \
            "the redirect target was never requested"
        assert proxy.received("http://127.0.0.1:65012/next", "Authorization") is None


def test_foreign_host_redirect_withholds_cookie():
    with RecordingServer() as proxy:
        proxy.redirect("http://127.0.0.1:65013/start", "http://127.0.0.1:65014/next")
        proxy.ok("http://127.0.0.1:65014/next")
        pool = _pool_as_proxy(proxy)
        try:
            response = pool.urlopen("GET", "http://127.0.0.1:65013/start",
                                    headers=dict(COOKIE), assert_same_host=False,
                                    redirect=True, timeout=10)
        finally:
            pool.close()
        assert response.status == 200
        assert proxy.requests_to("http://127.0.0.1:65014/next"), \
            "the redirect target was never requested"
        assert proxy.received("http://127.0.0.1:65014/next", "Cookie") is None
