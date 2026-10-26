"""The connection-pool entry point keeps working for ordinary and same-origin use."""

from __future__ import absolute_import

from urllib3 import HTTPConnectionPool

from support.harness import RecordingServer

AUTHORIZATION = {"Authorization": "Bearer legit-auth-9e02"}


def test_same_origin_redirect_keeps_credentials():
    with RecordingServer() as proxy:
        proxy.redirect("http://127.0.0.1:65021/start", "http://127.0.0.1:65021/next")
        proxy.ok("http://127.0.0.1:65021/next")
        pool = HTTPConnectionPool("127.0.0.1", proxy.port)
        try:
            response = pool.urlopen("GET", "http://127.0.0.1:65021/start",
                                    headers=dict(AUTHORIZATION), assert_same_host=False,
                                    redirect=True, timeout=10)
        finally:
            pool.close()
        assert response.status == 200
        assert proxy.received("http://127.0.0.1:65021/next", "Authorization") == \
            AUTHORIZATION["Authorization"]


def test_plain_request_through_a_foreign_host_is_answered():
    with RecordingServer() as proxy:
        proxy.ok("http://127.0.0.1:65022/resource", body=b"plain-body")
        pool = HTTPConnectionPool("127.0.0.1", proxy.port)
        try:
            response = pool.urlopen("GET", "http://127.0.0.1:65022/resource",
                                    headers=dict(AUTHORIZATION), assert_same_host=False,
                                    redirect=True, timeout=10)
        finally:
            pool.close()
        assert response.status == 200
        assert response.data == b"plain-body"
        assert proxy.received("http://127.0.0.1:65022/resource", "Authorization") == \
            AUTHORIZATION["Authorization"]
