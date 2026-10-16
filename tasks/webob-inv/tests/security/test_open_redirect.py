"""Security tests: a redirect target must never be smuggled off-host.

Each test drives a real public entry point of the library the way a
downstream web application would, supplies a redirect/resolution target that
LOOKS like a harmless same-host reference to the application's own guards, and
asserts that the value the client is ultimately told to go to still points at
the application's own host (``localhost``) rather than the attacker's host.

On vulnerable code the resolver silently removes leading control/space
characters, turning the reference into a protocol-relative or absolute URL, so
these assertions fail. A correct fix keeps every one of them on-host.
"""
from urllib.parse import urlsplit

import pytest

from webob import Request, Response
from webob.exc import HTTPFound

ATTACKER_HOST = "evil.example"
REQUEST_PATH = "/app/page"


def _request():
    # A request handled by an application mounted at /app/page on localhost.
    return Request.blank(REQUEST_PATH)


def _assert_on_host(location):
    """The browser-visible redirect target must stay on the request's host."""
    assert location is not None
    host = urlsplit(location).hostname
    # Either a same-host absolute URL or a host-less (relative) URL is fine;
    # anything resolving to the attacker's host is an open redirect.
    assert host != ATTACKER_HOST, f"open redirect to {host!r}: {location!r}"
    assert host in (None, "", "localhost"), f"off-site redirect: {location!r}"


def _response_location(raw_location):
    """Entry point 1: a Response with a Location header, run as a WSGI app."""
    resp = Response(status=302)
    resp.location = raw_location
    final = _request().get_response(resp)
    return final.location


def _httpexception_location(raw_location):
    """Entry point 2: an HTTP redirect exception called as a WSGI app."""
    environ = _request().environ
    captured = {}

    def start_response(status, headers, exc_info=None):
        captured["headers"] = headers

    HTTPFound(location=raw_location)(environ, start_response)
    return dict(captured["headers"]).get("Location")


def _relative_url(raw_reference):
    """Entry point 3: resolving a reference against the request URL."""
    return _request().relative_url(raw_reference)


# --- Entry point 1: Response Location header --------------------------------

def test_response_leading_space_protocol_relative():
    _assert_on_host(_response_location(" //" + ATTACKER_HOST + "/x"))


def test_response_leading_c0_control_protocol_relative():
    _assert_on_host(_response_location("\x01//" + ATTACKER_HOST + "/x"))


def test_response_leading_space_before_scheme():
    # Leading space before a scheme defeats a naive "strip then re-check"
    # fix: stripping turns it into an absolute URL the scheme guard trusts.
    _assert_on_host(_response_location(" https://" + ATTACKER_HOST + "/x"))


# --- Entry point 2: HTTP redirect exception (HTTPFound) ---------------------

def test_exception_leading_space_protocol_relative():
    _assert_on_host(_httpexception_location(" //" + ATTACKER_HOST + "/x"))


# test_exception_bare_protocol_relative removed 2026-10-16: an explicit "//host/x" is outside the
# instruction's requirement ("not an explicitly protocol-relative reference"); the test contradicted it.


def test_exception_leading_tab_protocol_relative():
    _assert_on_host(_httpexception_location("\t//" + ATTACKER_HOST + "/x"))


def test_exception_leading_space_before_scheme():
    _assert_on_host(_httpexception_location(" https://" + ATTACKER_HOST + "/x"))


# --- Entry point 3: request-relative URL resolution -------------------------

def test_relative_url_leading_space_protocol_relative():
    _assert_on_host(_relative_url(" //" + ATTACKER_HOST + "/x"))


def test_relative_url_leading_c0_control_protocol_relative():
    _assert_on_host(_relative_url("\x01//" + ATTACKER_HOST + "/x"))


def test_relative_url_leading_space_before_scheme():
    _assert_on_host(_relative_url(" https://" + ATTACKER_HOST + "/x"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
