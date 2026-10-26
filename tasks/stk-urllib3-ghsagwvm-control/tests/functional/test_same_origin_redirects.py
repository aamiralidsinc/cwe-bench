"""Redirects that stay on one origin keep every request header."""

from __future__ import absolute_import

from urllib3 import PoolManager

from support.harness import RecordingServer

AUTHORIZATION = {"Authorization": "Bearer legit-auth-31d0"}
COOKIE = {"Cookie": "session=legit-cookie-88f4"}
REQUEST_ID = {"X-Request-Id": "req-5512"}


def test_relative_redirect_keeps_credentials():
    with RecordingServer() as origin:
        origin.redirect("/start", "/next")
        origin.ok("/next")
        headers = dict(AUTHORIZATION)
        headers.update(COOKIE)
        response = PoolManager().request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                         headers=headers, timeout=10)
        assert response.status == 200
        assert origin.received("/next", "Authorization") == AUTHORIZATION["Authorization"]
        assert origin.received("/next", "Cookie") == COOKIE["Cookie"]


def test_host_case_redirect_keeps_credentials():
    with RecordingServer() as origin:
        origin.redirect("/start", "http://LOCALHOST:%d/next" % origin.port)
        origin.ok("/next")
        response = PoolManager().request("GET", "http://localhost:%d/start" % origin.port,
                                         headers=dict(AUTHORIZATION), timeout=10)
        assert response.status == 200
        assert origin.received("/next", "Authorization") == AUTHORIZATION["Authorization"]


def test_redirect_without_credentials_is_still_followed():
    with RecordingServer() as origin:
        origin.redirect("/start", "/final")
        origin.ok("/final", body=b"final-body")
        response = PoolManager().request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                         timeout=10)
        assert response.status == 200
        assert response.data == b"final-body"


def test_non_credential_headers_survive_a_cross_origin_redirect():
    with RecordingServer() as origin, RecordingServer() as other:
        origin.redirect("/start", "http://127.0.0.1:%d/next" % other.port)
        other.ok("/next", body=b"other-body")
        response = PoolManager().request("GET", "http://127.0.0.1:%d/start" % origin.port,
                                         headers=dict(REQUEST_ID), timeout=10)
        assert response.status == 200
        assert response.data == b"other-body"
        assert other.received("/next", "X-Request-Id") == REQUEST_ID["X-Request-Id"]
