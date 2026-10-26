"""Credentials must not follow a redirect to another origin (URLFetch-backed manager)."""

from __future__ import absolute_import

import warnings

import pytest

from support.harness import install_urlfetch_stub

STUB = install_urlfetch_stub()

from urllib3.contrib import appengine  # noqa: E402  (imported after the stub is registered)

AUTHORIZATION = {"Authorization": "Bearer marker-auth-5b09"}
COOKIE = {"Cookie": "session=marker-cookie-7a13"}


def _manager():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return appengine.AppEngineManager()


@pytest.fixture(autouse=True)
def _clean_stub():
    STUB.calls[:] = []
    STUB.routes.clear()


def test_cross_origin_redirect_withholds_authorization():
    STUB.route("http://origin-a.test/start", status=302,
               location="http://origin-b.test/next")
    STUB.route("http://origin-b.test/next", status=200, body=b"ok")
    response = _manager().request("GET", "http://origin-a.test/start",
                                  headers=dict(AUTHORIZATION))
    assert response.status == 200
    assert STUB.headers_for("http://origin-b.test/next") is not None, \
        "the redirect target was never requested"
    assert STUB.received("http://origin-b.test/next", "Authorization") is None


def test_cross_origin_redirect_withholds_cookie():
    STUB.route("http://origin-c.test/start", status=302,
               location="http://origin-d.test/next")
    STUB.route("http://origin-d.test/next", status=200, body=b"ok")
    response = _manager().request("GET", "http://origin-c.test/start", headers=dict(COOKIE))
    assert response.status == 200
    assert STUB.headers_for("http://origin-d.test/next") is not None, \
        "the redirect target was never requested"
    assert STUB.received("http://origin-d.test/next", "Cookie") is None
