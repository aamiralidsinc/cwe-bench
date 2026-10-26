"""The URLFetch-backed manager keeps working for ordinary and same-origin use."""

from __future__ import absolute_import

import warnings

import pytest

from support.harness import install_urlfetch_stub

STUB = install_urlfetch_stub()

from urllib3.contrib import appengine  # noqa: E402  (imported after the stub is registered)

AUTHORIZATION = {"Authorization": "Bearer legit-auth-6d40"}


def _manager():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return appengine.AppEngineManager()


@pytest.fixture(autouse=True)
def _clean_stub():
    STUB.calls[:] = []
    STUB.routes.clear()


def test_same_origin_redirect_keeps_credentials():
    STUB.route("http://origin-e.test/start", status=302, location="/next")
    STUB.route("http://origin-e.test/next", status=200, body=b"same-origin")
    response = _manager().request("GET", "http://origin-e.test/start",
                                  headers=dict(AUTHORIZATION))
    assert response.status == 200
    assert response.data == b"same-origin"
    assert STUB.received("http://origin-e.test/next", "Authorization") == \
        AUTHORIZATION["Authorization"]


def test_plain_request_returns_the_response():
    STUB.route("http://origin-f.test/resource", status=200, body=b"plain-body")
    response = _manager().request("GET", "http://origin-f.test/resource",
                                  headers=dict(AUTHORIZATION))
    assert response.status == 200
    assert response.data == b"plain-body"
    assert STUB.received("http://origin-f.test/resource", "Authorization") == \
        AUTHORIZATION["Authorization"]
