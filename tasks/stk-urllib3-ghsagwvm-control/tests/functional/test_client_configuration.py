"""A client's configured request headers keep being sent where they are legitimate."""

from __future__ import absolute_import

from urllib3 import PoolManager

from support.harness import RecordingServer

AUTHORIZATION = {"Authorization": "Bearer configured-2f55"}


def test_configured_headers_are_sent_on_every_call():
    with RecordingServer() as origin:
        origin.ok("/first")
        origin.ok("/second")
        client = PoolManager(headers=dict(AUTHORIZATION))
        first = client.request("GET", "http://127.0.0.1:%d/first" % origin.port, timeout=10)
        second = client.request("GET", "http://127.0.0.1:%d/second" % origin.port, timeout=10)
        assert first.status == 200 and second.status == 200
        assert origin.received("/first", "Authorization") == AUTHORIZATION["Authorization"]
        assert origin.received("/second", "Authorization") == AUTHORIZATION["Authorization"]


def test_configured_headers_survive_a_same_origin_redirect():
    with RecordingServer() as origin:
        origin.redirect("/start", "/next")
        origin.ok("/next")
        client = PoolManager(headers=dict(AUTHORIZATION))
        response = client.request("GET", "http://127.0.0.1:%d/start" % origin.port, timeout=10)
        assert response.status == 200
        assert origin.received("/next", "Authorization") == AUTHORIZATION["Authorization"]
